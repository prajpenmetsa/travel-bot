# Requirements Specification Document
## Travel Itinerary Pitcher

### Project Overview
The Travel Itinerary Pitcher is a GenAI-powered application that creates personalized, narrative-style travel itineraries based on user preferences. Unlike typical travel planning tools that provide generic lists of attractions, this application crafts compelling "pitches" that tell a story about the user's potential journey, highlighting unique experiences that match their specific interests.

### User Requirements

#### User Stories
1. As a traveler, I want to input my destination, interests, budget, and trip duration so that I can get personalized travel recommendations.
2. As a traveler, I want to receive a compelling narrative about my potential trip so that I can get excited about the destination.
3. As a traveler, I want to see a day-by-day breakdown of activities so that I can understand how my trip might flow.
4. As a traveler, I want budget estimates for my trip so that I can plan my finances accordingly.
5. As a traveler, I want suggestions that match my specific interests so that my trip feels personalized.

#### User Inputs
- **Destination**: City or country name
- **Interests**: Multiple selections from predefined categories (history, food, adventure, culture, nature, relaxation, shopping, nightlife, family)
- **Budget Level**: Selection from three options (budget, moderate, luxury)
- **Trip Duration**: Number of days (1-14)

#### User Outputs
- **Narrative Pitch**: A compelling story-like description of the potential trip
- **Day-by-Day Plan**: Structured itinerary with themed days and activities
- **Budget Breakdown**: Estimated costs by category and per day

### Functional Requirements

#### Core Functionality
1. **F1**: Process and validate user inputs
2. **F2**: Retrieve or generate destination information
3. **F3**: Suggest experiences based on user interests and destination
4. **F4**: Calculate budget estimates based on destination and preferences
5. **F5**: Generate a compelling narrative pitch
6. **F6**: Present information in an organized, user-friendly interface

#### Microservices
1. **User Preference Service**
   - **F1.1**: Validate and standardize location input
   - **F1.2**: Process interest selections
   - **F1.3**: Validate budget and duration inputs

2. **Location Data Service**
   - **F2.1**: Retrieve destination information
   - **F2.2**: Generate missing information using GenAI
   - **F2.3**: Cache results for repeated queries

3. **Experience Suggestion Service**
   - **F3.1**: Match user interests to appropriate activities
   - **F3.2**: Create a balanced day-by-day plan
   - **F3.3**: Assign appropriate times of day for activities

4. **Budget Service**
   - **F4.1**: Calculate accommodation cost estimates
   - **F4.2**: Calculate food cost estimates
   - **F4.3**: Calculate transportation cost estimates
   - **F4.4**: Calculate activity cost estimates
   - **F4.5**: Provide total and per-day budgets

5. **Narrative Generation Service**
   - **F5.1**: Generate compelling travel narrative
   - **F5.2**: Incorporate specific experiences into the narrative
   - **F5.3**: Adjust tone for the user's interests

6. **Frontend Service**
   - **F6.1**: Provide intuitive input interface
   - **F6.2**: Display narrative in an engaging format
   - **F6.3**: Show day-by-day breakdown
   - **F6.4**: Present budget information visually

7. **Evaluation Service**
   - **F7.1**: Compute sub-scores (interest coverage, daily pacing, diversity, budget realism, region realism, narrative quality, feasibility)
   - **F7.2**: Apply configurable weights and return a single 0-100 composite score
   - **F7.3**: Expose per-metric breakdown so the UI can explain why a trip earned its score
   - **F7.4**: Accept plug-in baselines / heuristics (e.g., city cost tables) without changing core logic
   - **F7.5**: Gracefully degrade when optional GenAI sentiment check is unavailable (defaults to neutral score)

8. **Itinerary Chat Service**
   - **F8.1**: start_session() – load narrative + budget into context and return a unique chat_id
   - **F8.2**: answer(chat_id, question) – generate Gemini-powered replies, scoped to the user’s itinerary
   - **F8.3**: Detect general-knowledge vs itinerary-specific queries and adapt the prompt accordingly
   - **F8.4**: Scrape & cache supporting web content (respect robots.txt, rotate user-agents, retry with back-off)
   - **F8.5**: Maintain short chat history for follow-up context and allow reset_conversation() to clear it

### Non-Functional Requirements

1. **Performance**
   - **NF1.1**: Generate results within 15 seconds (per day inputted)
   - **NF1.2**: Support multiple concurrent users

2. **Usability**
   - **NF2.1**: Interface should be intuitive for non-technical users
   - **NF2.2**: Clear instructions and feedback throughout the process

3. **Reliability**
   - **NF3.1**: Graceful fallback if GenAI services are unavailable
   - **NF3.2**: Error handling for invalid inputs

4. **Maintainability**
   - **NF4.1**: Modular code structure
   - **NF4.2**: Clear documentation

5. **Security**
   - **NF5.1**: No storage of sensitive user data
   - **NF5.2**: Secure API key handling

### Technical Requirements

1. **Technology Stack**
   - **T1.1**: Python-based backend
   - **T1.2**: Streamlit for frontend
   - **T1.3**: OpenAI API for GenAI capabilities
   - **T1.4**: Local file storage for simple persistence

2. **Architecture**
   - **T2.1**: Microservices architecture
   - **T2.2**: HTTP APIs for service communication
   - **T2.3**: Cloud-native deployment ready

3. **Integration**
   - **T3.1**: OpenAI API integration
   - **T3.2**: Optional: Integration with external travel data APIs (future enhancement)

### Constraints

1. **Time**: Must be implementable within 3-day hackathon
2. **Cost**: Should use free-tier services
3. **Knowledge**: Should be implementable with standard Python libraries and basic GenAI knowledge

### Evaluation Criteria

1. **Functionality**: Does the system generate compelling, personalized travel narratives?
2. **Usability**: Is the interface intuitive and the output engaging?
3. **Technical Implementation**: Is the microservices architecture properly implemented?
4. **GenAI Usage**: Is GenAI effectively leveraged throughout the system?
5. **Completeness**: Is the MVP fully functional end-to-end?