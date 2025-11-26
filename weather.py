import streamlit as st
import requests
from datetime import datetime
import pandas as pd
from gtts import gTTS
import base64
import io

# Page configuration
st.set_page_config(page_title="Weather Dashboard", page_icon="🌤️", layout="wide")

# Get API key from secrets.toml
try:
    API_KEY = st.secrets["OPENWEATHER_API_KEY"]
except KeyError:
    st.error("⚠️ API key not found! Please add OPENWEATHER_API_KEY to your secrets.toml file.")
    st.info("""
    **To fix this:**
    1. Create a `.streamlit` folder in your project directory
    2. Create a `secrets.toml` file inside it
    3. Add this line: `OPENWEATHER_API_KEY = "your_api_key_here"`
    """)
    st.stop()

BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"

def get_weather(city):
    """Fetch current weather data for a city"""
    # Clean and format the city name
    city_cleaned = city.strip()
    
    # Try different formatting variations
    city_variations = [
        city_cleaned,          # Original input (e.g., "Paris, France")
        city_cleaned.title(),  # Title Case: "Paris, France"
        city_cleaned.upper(),  # Upper Case: "PARIS, FRANCE"
        city_cleaned.lower(),  # Lower Case: "paris, france"
    ]
    
    for city_try in city_variations:
        params = {
            'q': city_try,
            'appid': API_KEY,
            'units': 'metric'
        }
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException:
            continue
    
    # If all variations failed, return error
    return {'cod': 404, 'message': 'City not found'}

def get_forecast(city):
    """Fetch 5-day forecast data for a city"""
    # Clean and format the city name
    city_cleaned = city.strip()
    
    # Try different formatting variations
    city_variations = [
        city_cleaned,          # Original input (e.g., "Paris, France")
        city_cleaned.title(),  # Title Case: "Paris, France"
        city_cleaned.upper(),  # Upper Case: "PARIS, FRANCE"
        city_cleaned.lower(),  # Lower Case: "paris, france"
    ]
    
    for city_try in city_variations:
        params = {
            'q': city_try,
            'appid': API_KEY,
            'units': 'metric'
        }
        try:
            response = requests.get(FORECAST_URL, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException:
            continue
    
    # If all variations failed, return error
    return {'cod': '404', 'message': 'City not found'}

def display_current_weather(data):
    """Display current weather information"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🌡️ Temperature",
            value=f"{data['main']['temp']:.1f}°C",
            delta=f"Feels like {data['main']['feels_like']:.1f}°C"
        )
    
    with col2:
        st.metric(
            label="💧 Humidity",
            value=f"{data['main']['humidity']}%"
        )
    
    with col3:
        st.metric(
            label="💨 Wind Speed",
            value=f"{data['wind']['speed']} m/s"
        )
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric(
            label="🔽 Pressure",
            value=f"{data['main']['pressure']} hPa"
        )
    
    with col5:
        st.metric(
            label="👁️ Visibility",
            value=f"{data.get('visibility', 0) / 1000:.1f} km"
        )
    
    with col6:
        weather_desc = data['weather'][0]['description'].title()
        st.metric(
            label="☁️ Condition",
            value=weather_desc
        )

def display_forecast(data):
    """Display 5-day forecast"""
    st.subheader("📅 5-Day Forecast")
    
    forecast_list = data['list'][::8]  # Get one forecast per day (every 8th entry = 24 hours)
    
    dates = []
    temps = []
    descriptions = []
    
    for item in forecast_list[:5]:
        date = datetime.fromtimestamp(item['dt']).strftime('%a, %b %d')
        temp = item['main']['temp']
        desc = item['weather'][0]['description'].title()
        
        dates.append(date)
        temps.append(temp)
        descriptions.append(desc)
    
    # Create dataframe for forecast
    df = pd.DataFrame({
        'Date': dates,
        'Temperature (°C)': temps,
        'Condition': descriptions
    })
    
    # Display as chart
    st.line_chart(df.set_index('Date')['Temperature (°C)'])
    
    # Display as table
    st.dataframe(df, use_container_width=True, hide_index=True)

def get_clothing_advice(temp, condition, humidity):
    """Generate clothing advice based on weather conditions"""
    advice = []
    stay_indoor = False
    
    # Temperature-based advice
    if temp < -10:
        advice.append("It's extremely cold outside. Wear heavy winter coat, thermal layers, gloves, scarf, and winter hat.")
        stay_indoor = True
    elif temp < 0:
        advice.append("It's freezing cold. Wear a heavy jacket, warm layers, gloves, and a hat.")
    elif temp < 10:
        advice.append("It's quite cold. Wear a warm jacket, long sleeves, and consider bringing a scarf.")
    elif temp < 15:
        advice.append("It's cool outside. A light jacket or sweater would be comfortable.")
    elif temp < 20:
        advice.append("The weather is mild. A light sweater or long sleeves should be perfect.")
    elif temp < 25:
        advice.append("It's pleasant outside. Comfortable clothing like a t-shirt and light pants works well.")
    elif temp < 30:
        advice.append("It's warm. Wear light, breathable clothing like shorts and t-shirts.")
    elif temp < 35:
        advice.append("It's hot outside. Wear minimal, light-colored, breathable clothing and stay hydrated.")
    else:
        advice.append("It's extremely hot! Wear very light clothing, stay hydrated, and avoid prolonged sun exposure.")
        stay_indoor = True
    
    # Condition-based advice
    condition_lower = condition.lower()
    if 'rain' in condition_lower or 'drizzle' in condition_lower:
        advice.append("Don't forget your umbrella and waterproof jacket!")
    elif 'snow' in condition_lower:
        advice.append("Wear waterproof boots and be careful of slippery surfaces.")
    elif 'storm' in condition_lower or 'thunder' in condition_lower:
        advice.append("There's a storm warning. It's safer to stay indoors if possible!")
        stay_indoor = True
    elif 'fog' in condition_lower or 'mist' in condition_lower:
        advice.append("Visibility is low. Drive carefully and wear visible clothing.")
    
    # Humidity-based advice
    if humidity > 80:
        advice.append("High humidity today. Wear moisture-wicking fabrics to stay comfortable.")
    
    return advice, stay_indoor

def generate_weather_speech(city, temp, feels_like, condition, advice_list, stay_indoor):
    """Generate speech text for weather report"""
    speech_text = f"Weather report for {city}. "
    speech_text += f"The current temperature is {temp:.1f} degrees Celsius, "
    speech_text += f"but it feels like {feels_like:.1f} degrees. "
    speech_text += f"The weather condition is {condition}. "
    
    if stay_indoor:
        speech_text += "Warning! Weather conditions are extreme. It is strongly advised to stay indoors. "
    
    speech_text += "Here's what you should wear. " + " ".join(advice_list)
    
    return speech_text

def text_to_speech(text):
    """Convert text to speech and return audio HTML"""
    try:
        # Create gTTS object
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save to BytesIO object
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Encode to base64
        audio_base64 = base64.b64encode(audio_buffer.read()).decode()
        
        # Create HTML audio player
        audio_html = f"""
        <audio controls autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        return audio_html
    except Exception as e:
        return None

# Main app
st.title("🌤️ Weather Dashboard")
st.markdown("Get real-time weather information for any city worldwide")

# City input
col1, col2 = st.columns([3, 1])
with col1:
    city = st.text_input("Enter city name", value="London", placeholder="e.g., new york, tokyo, paris, kuala lumpur")
with col2:
    st.write("")
    st.write("")
    search_button = st.button("🔍 Search", use_container_width=True)

if city and city.strip() and (search_button or 'last_city' not in st.session_state or st.session_state.last_city != city):
    st.session_state.last_city = city
    st.session_state.weather_loaded = False
    st.session_state.search_attempted = True
    
    with st.spinner(f"Fetching weather data for {city.strip()}..."):
        weather_data = get_weather(city)
        forecast_data = get_forecast(city)
    
    if weather_data and weather_data.get('cod') == 200:
        st.session_state.weather_data = weather_data
        st.session_state.forecast_data = forecast_data
        st.session_state.weather_loaded = True
        st.session_state.error_data = None
    else:
        st.session_state.weather_loaded = False
        st.session_state.error_data = weather_data

# Display weather if available
if st.session_state.get('weather_loaded', False):
    weather_data = st.session_state.weather_data
    forecast_data = st.session_state.forecast_data
    
    # Display city info
    st.success(f"Weather in **{weather_data['name']}, {weather_data['sys']['country']}**")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    st.divider()
    
    # Current weather
    st.subheader("🌍 Current Weather")
    display_current_weather(weather_data)
    
    st.divider()
    
    # Clothing advice section
    st.subheader("👔 Clothing Advice")
    temp = weather_data['main']['temp']
    feels_like = weather_data['main']['feels_like']
    condition = weather_data['weather'][0]['description'].title()
    humidity = weather_data['main']['humidity']
    
    advice_list, stay_indoor = get_clothing_advice(temp, condition, humidity)
    
    if stay_indoor:
        st.warning("⚠️ **EXTREME WEATHER ALERT!** It's recommended to stay indoors if possible.")
    
    for advice in advice_list:
        st.info(advice)
    
    st.divider()
    
    # Voice announcement section
    st.subheader("🔊 Voice Weather Report")
    
    play_voice = st.button("▶️ Play Report", use_container_width=False, key="play_voice_btn")
    
    if play_voice:
        with st.spinner("Generating voice report..."):
            speech_text = generate_weather_speech(
                weather_data['name'],
                temp,
                feels_like,
                condition,
                advice_list,
                stay_indoor
            )
            
            audio_html = text_to_speech(speech_text)
            
            if audio_html:
                st.markdown(audio_html, unsafe_allow_html=True)
                with st.expander("📝 View Report Text"):
                    st.write(speech_text)
            else:
                st.error("Failed to generate voice report. Please try again.")
    
    st.divider()
    
    # Forecast
    if forecast_data and forecast_data.get('cod') == '200':
        display_forecast(forecast_data)
    else:
        st.warning("Forecast data unavailable")
        
elif st.session_state.get('search_attempted') and st.session_state.get('error_data'):
    # Show error if search was attempted but failed
    error_data = st.session_state.error_data
    error_msg = error_data.get('message', 'Unknown error') if error_data else 'No response from server'
    
    # Check if it's likely a spelling issue
    if 'not found' in error_msg.lower() or error_data.get('cod') == 404:
        st.error(f"❌ City '{st.session_state.last_city}' not found. Please verify the city name exists.")
        st.info("💡 **Tip:** If the city has a common name, try adding the country (e.g., 'Asaba, Nigeria' or 'Paris, France')")
    else:
        st.error(f"❌ Error: {error_msg}")
        if 'Invalid API key' in str(error_msg):
            st.warning("⚠️ Please check that your API key is correctly configured in Streamlit secrets.")

# Footer
st.divider()
st.caption("Data provided by OpenWeatherMap API | Weather Dashboard v1.0")
