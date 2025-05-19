import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

class ItineraryDecoderService:
    def __init__(self, model_path="./qwen_lora_itinerary/final"):
        """Initialize the itinerary decoder service with the fine-tuned model."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load base model and tokenizer
        base_model_name = "Qwen/Qwen1.5-0.5B"
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
        
        # Load the fine-tuned model
        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_name, 
            trust_remote_code=True,
            device_map="auto"
        )
        
        # Load the LoRA weights
        self.model = PeftModel.from_pretrained(self.model, model_path)
        self.model.eval()
    
    def format_prompt(self, destination, duration, budget, core_prefs, special_prefs):
        """Format the input prompt for the model."""
        return (
            f"Generate a {duration}-day itinerary for {destination} "
            f"with budget '{budget}' and preferences:\n"
            f"Core: {core_prefs}\n"
            f"Special: {special_prefs}\n\nItinerary:"
        )
    
    def generate_itinerary(self, destination, duration, budget, core_prefs, special_prefs, 
                          max_length=1024, temperature=0.7):
        """Generate an itinerary based on the given parameters."""
        prompt = self.format_prompt(destination, duration, budget, core_prefs, special_prefs)
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=temperature,
                top_p=0.9,
                do_sample=True
            )
        
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the generated itinerary by removing the prompt
        itinerary = full_response[len(prompt):]
        
        return itinerary.strip()

# Example usage
if __name__ == "__main__":
    service = ItineraryDecoderService()
    
    # Test with a sample request
    itinerary = service.generate_itinerary(
        destination="Paris, France",
        duration="3",
        budget="Medium",
        core_prefs="Culture, Food",
        special_prefs="Art museums, Local cuisine"
    )
    
    print(itinerary)