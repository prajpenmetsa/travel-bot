"""
Evaluation Service
──────────────────
Scores an itinerary and its budget on a 0-100 rubric.

Public use:
    from evaluation_service import EvaluationService
    scores = EvaluationService().score(prefs, narrative, budget)

`scores` looks like
{
    "interest_coverage": 0.75,
    "daily_pacing": 0.8,
    "diversity": 0.66,
    "budget_realism": 0.92,
    "region_realism": 0.83,
    "narrative_quality": 0.6,
    "feasibility": 0.5,
    "total": 78.9
}
"""

from __future__ import annotations
import re
from collections import Counter
from typing import Dict, List, Any

# Optional LLM check (if you have a Gemini key in env / config.json)
try:
    import google.generativeai as genai          # type: ignore
except ModuleNotFoundError:
    genai = None


class EvaluationService:
    # ---------- tweakable weights ----------
    WEIGHTS = {
        "interest_coverage": 0.25,
        "daily_pacing":      0.15,
        "diversity":         0.10,
        "budget_realism":    0.20,
        "region_realism":    0.10,
        "narrative_quality": 0.10,
        "feasibility":       0.10,
    }

    IDEAL_ACTIVITIES = (3, 6)        # per day (min, max)

    REGION_BASELINE_USD = {          # average backpacker daily spend
        "paris": 150,
        "bangkok": 50,
        "new york": 200,
        "tokyo": 180,
        "london": 170,
    }

    # ---------- public ----------
    def score(
        self,
        prefs: Dict[str, Any],
        narrative: Dict[str, Any],
        budget: Dict[str, Any],
    ) -> Dict[str, Any]:
        subs = {
            "interest_coverage": self._interest_coverage(prefs, narrative),
            "daily_pacing":      self._daily_pacing(narrative),
            "diversity":         self._diversity(narrative),
            "budget_realism":    self._budget_realism(narrative, budget),
            "region_realism":    self._region_realism(prefs, budget),
            "narrative_quality": self._narrative_quality(narrative) if genai else 0.5,
            "feasibility":       0.5,     # placeholder until you add open-hour data
        }
        total = sum(subs[k] * w * 100 for k, w in self.WEIGHTS.items())
        subs["total"] = round(total, 1)
        return subs

    # ---------- sub-metrics ----------
    def _interest_coverage(self, prefs, nar) -> float:
        txt = " ".join(d["content"] for d in nar["daily_plans"]).lower()
        hits = sum(1 for i in prefs["interests"] if i.lower() in txt)
        return hits / max(len(prefs["interests"]), 1)

    def _daily_pacing(self, nar) -> float:
        low, high = self.IDEAL_ACTIVITIES
        ok = 0
        for d in nar["daily_plans"]:
            n = len(re.findall(r"^\s*(?:\*|-|\d+\.)", d["content"], flags=re.M))
            ok += low <= n <= high
        return ok / len(nar["daily_plans"])

    def _diversity(self, nar) -> float:
        acts: list[str] = []
        for d in nar["daily_plans"]:
            acts += re.findall(r"\[(.*?)\]", d["content"])
        if not acts:
            return 0.5
        uniq_ratio = len(set(acts)) / len(acts)
        return min(1.0, uniq_ratio * 3)

    def _budget_realism(self, nar, budget) -> float:
        txt_total = self._extract_usd(nar["budget_narrative"])
        calc_total = budget["total"]["grand_total"]
        if txt_total is None:
            return 0.3
        diff = abs(txt_total - calc_total) / calc_total
        return max(0.0, 1 - diff)

    def _region_realism(self, prefs, budget) -> float:
        city = prefs["destination"].split(",")[0].lower()
        base = self.REGION_BASELINE_USD.get(city)
        if base is None:
            return 0.5
        actual = budget["per_day"]["total_daily"]
        ratio = actual / base
        return 1 - min(abs(ratio - 1), 1)

    def _narrative_quality(self, nar) -> float:
        prompt = (
            "Rate the clarity and engagement of this itinerary narrative "
            "from 1 (poor) to 5 (excellent). Return only the number.\n\n"
            f"{nar['main_narrative']}"
        )
        try:
            resp = genai.GenerativeModel("gemini-2.0-flash").generate_content(prompt)
            score = int(re.search(r"[1-5]", resp.text).group())
            return (score - 1) / 4
        except Exception:           # network or parse error
            return 0.5

    # ---------- helpers ----------
    @staticmethod
    def _extract_usd(text: str) -> float | None:
        m = re.search(r"\$([0-9][0-9,]*)", text)
        return float(m.group(1).replace(",", "")) if m else None
