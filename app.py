from flask import Flask,render_template,request,jsonify,session
from dotenv import load_dotenv
from google import genai
import requests,math,os,re

load_dotenv()
app=Flask(__name__,template_folder=".",static_folder=".",static_url_path="")
app.secret_key="voyageai-secret-key-2026"

GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
gemini_client=None

if GEMINI_API_KEY:
    try:
        gemini_client=genai.Client(api_key=GEMINI_API_KEY)
        print("========================================")
        print("Gemini API connected successfully")
        print("Model: gemini-3.6-flash")
        print("========================================")
    except Exception as e:
        print("Gemini connection error:")
        print(e)
else:
    print("========================================")
    print("Gemini API key not found")
    print("========================================")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/planner")
def planner():
    return render_template("planner.html")

def haversine(lat1,lon1,lat2,lon2):
    radius=6371
    lat1,lat2=math.radians(lat1),math.radians(lat2)
    dlat=math.radians(lat2-lat1)
    dlon=math.radians(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return radius*2*math.atan2(math.sqrt(a),math.sqrt(1-a))

def geocode_location(query):
    url="https://nominatim.openstreetmap.org/search"
    params={"q":query,"format":"json","limit":1}
    headers={"User-Agent":"VoyageAI-Trip-Planner/1.0"}
    response=requests.get(url,params=params,headers=headers,timeout=20)
    response.raise_for_status()
    data=response.json()
    if not data:return None
    return {"name":data[0].get("display_name",query),"lat":float(data[0]["lat"]),"lon":float(data[0]["lon"])}

def get_places(lat,lon):
    servers=[
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]
    query=f"""
    [out:json][timeout:35];
    (
    nwr["tourism"="attraction"](around:30000,{lat},{lon});
    nwr["tourism"="museum"](around:30000,{lat},{lon});
    nwr["tourism"="viewpoint"](around:30000,{lat},{lon});
    nwr["tourism"="zoo"](around:30000,{lat},{lon});
    nwr["tourism"="theme_park"](around:30000,{lat},{lon});
    nwr["historic"](around:30000,{lat},{lon});
    nwr["leisure"="park"](around:30000,{lat},{lon});
    nwr["natural"="beach"](around:30000,{lat},{lon});
    );
    out center tags;
    """
    headers={"User-Agent":"VoyageAI-Trip-Planner/1.0"}

    for server in servers:
        try:
            response=requests.post(server,data=query,headers=headers,timeout=50)
            response.raise_for_status()
            data=response.json()
            places=[]

            for item in data.get("elements",[]):
                tags=item.get("tags",{})
                name=tags.get("name")
                if not name:continue

                if "lat" in item:
                    place_lat=float(item["lat"]);place_lon=float(item["lon"])
                elif "center" in item:
                    place_lat=float(item["center"]["lat"]);place_lon=float(item["center"]["lon"])
                else:continue

                places.append({
                    "name":name.strip(),
                    "lat":place_lat,
                    "lon":place_lon,
                    "distance":round(haversine(lat,lon,place_lat,place_lon),2),
                    "tourism":tags.get("tourism",""),
                    "historic":tags.get("historic",""),
                    "natural":tags.get("natural",""),
                    "leisure":tags.get("leisure",""),
                    "tags":[]
                })

            unique={p["name"].lower().strip():p for p in places}
            result=list(unique.values())
            result.sort(key=lambda x:x["distance"])
            print("Places found:",len(result))
            return result

        except Exception as error:
            print("Overpass failed:",error)

    print("All Overpass servers failed.")
    return []

def classify_place(place):
    tourism=place.get("tourism","").lower()
    historic=place.get("historic","").lower()
    natural=place.get("natural","").lower()
    leisure=place.get("leisure","").lower()
    categories=[]

    if tourism=="museum":categories+=["history","culture"]
    if tourism=="viewpoint":categories.append("nature")
    if tourism in ["zoo","theme_park"]:categories.append("adventure")
    if tourism=="attraction":categories.append("culture")
    if historic:categories+=["history","culture"]
    if natural=="beach":categories.append("nature")
    if leisure=="park":categories.append("nature")
    if not categories:categories.append("culture")

    return list(dict.fromkeys(categories))

def create_description(place):
    categories=classify_place(place)
    if "history" in categories:return "A historical and cultural place worth exploring."
    if "nature" in categories:return "A natural place suitable for exploration and relaxation."
    if "adventure" in categories:return "A destination suitable for fun and adventure."
    return "An interesting place to explore during your trip."

def calculate_ai_score(place,interests):
    score=0
    categories=classify_place(place)

    for interest in interests:
        if interest.lower() in categories:score+=20

    d=place["distance"]
    if d<=2:score+=10
    elif d<=5:score+=8
    elif d<=10:score+=6
    elif d<=20:score+=3
    else:score+=1

    tourism=place.get("tourism","")
    if tourism=="attraction":score+=5
    elif tourism in ["museum","viewpoint"]:score+=4
    elif tourism in ["zoo","theme_park"]:score+=3

    return score

def astar_route(start,places):
    if not places:return []
    remaining=places.copy()
    route=[]
    current=start

    while remaining:
        best_place=None
        best_f=float("inf")

        for place in remaining:
            g=haversine(current["lat"],current["lon"],place["lat"],place["lon"])
            others=[p for p in remaining if p!=place]
            h=min([haversine(place["lat"],place["lon"],p["lat"],p["lon"]) for p in others],default=0)
            f=g+h

            if f<best_f:
                best_f=f
                best_place=place

        if best_place is None:break
        route.append(best_place)
        remaining.remove(best_place)
        current=best_place

    return route

def create_full_itinerary(places,days,start):
    days=max(1,int(days))

    if not places:
        return [{"day":day,"places":[]} for day in range(1,days+1)]

    sorted_places=sorted(places,key=lambda x:x["ai_score"],reverse=True)
    selected=sorted_places[:min(len(sorted_places),days*4)]
    route=astar_route(start,selected)

    itinerary=[{"day":day,"places":[]} for day in range(1,days+1)]

    for index,place in enumerate(route):
        itinerary[index%days]["places"].append(place)

    return itinerary

def get_weather(lat,lon):
    url="https://api.open-meteo.com/v1/forecast"
    params={"latitude":lat,"longitude":lon,"current":"temperature_2m,weather_code","timezone":"auto"}
    response=requests.get(url,params=params,timeout=20)
    response.raise_for_status()
    current=response.json().get("current",{})
    return {"temperature":current.get("temperature_2m"),"weather_code":current.get("weather_code")}

def create_transport_options(start_location,destination,distance):
    distance=max(0,float(distance or 0))

    flight_cost=max(2500,2500+distance*5)
    train_cost=max(500,500+distance*1.7)
    bus_cost=max(350,350+distance*1.25)
    car_cost=max(800,800+distance*4)

    flight_time="Usually not practical" if distance<250 else "Approx. 1–2.5 hrs" if distance<700 else "Approx. 1–3 hrs"
    train_hours=max(2,distance/65)
    bus_hours=max(3,distance/50)
    car_hours=max(2,distance/55)

    options=[
        {"name":"Train","icon":"🚆","description":"A practical choice for many medium-distance journeys.","time":f"Approx. {train_hours:.1f} hrs","cost":f"₹{train_cost:,.0f}","link":"https://www.irctc.co.in/","recommended":False},
        {"name":"Bus","icon":"🚌","description":"A lower-cost option for road travel.","time":f"Approx. {bus_hours:.1f} hrs","cost":f"₹{bus_cost:,.0f}","link":"https://www.redbus.in/","recommended":False},
        {"name":"Flight","icon":"✈️","description":"Generally the fastest option for long-distance travel.","time":flight_time,"cost":f"₹{flight_cost:,.0f}","link":"https://www.google.com/travel/flights","recommended":False},
        {"name":"Car","icon":"🚗","description":"Flexible road travel with direct control over your route.","time":f"Approx. {car_hours:.1f} hrs","cost":f"₹{car_cost:,.0f}","link":"https://www.google.com/maps/","recommended":False}
    ]

    usable=[x for x in options if "not practical" not in x["time"]]

    if usable:
        cheapest=min(usable,key=lambda x:float(x["cost"].replace("₹","").replace(",","")))
        cheapest["recommended"]=True

    return options

def ask_gemini(message):
    if not gemini_client:
        return "Gemini is not connected. Please check your GEMINI_API_KEY inside the .env file."

    try:
        history=session.get("chat_history",[])
        chat=gemini_client.chats.create(model="gemini-3.6-flash",history=history)

        prompt=f"""
You are VoyageAI, an intelligent and friendly travel assistant.
Help users with:
- destinations
- itineraries
- food
- transportation
- budgets
- packing
- activities
- travel tips
Answer naturally.
Do not invent real tourist attraction names.
If the user asks for real tourist places in a destination, VoyageAI will search live OpenStreetMap data.
User message:
{message}
"""

        response=chat.send_message(prompt)
        reply=response.text
        new_history=[]

        for item in chat.get_history():
            try:
                if not item.parts:continue
                text=item.parts[0].text
                if not text:continue
                new_history.append({"role":item.role,"parts":[{"text":text}]})
            except Exception:
                continue

        session["chat_history"]=new_history[-20:]
        session.modified=True
        return reply

    except Exception as error:
        print("Gemini error:",error)
        return "Sorry, I couldn't connect to Gemini right now. Please try again."

def extract_destination(message):
    patterns=[
        r"show me places in (.+)",r"places in (.+)",
        r"tourist places in (.+)",r"tourist attractions in (.+)",
        r"what can i see in (.+)",r"what can i visit in (.+)",
        r"what should i see in (.+)",r"i want to go to (.+)",
        r"i want to visit (.+)",r"travel to (.+)",
        r"go to (.+)",r"trip to (.+)",r"visit (.+)"
    ]

    message_lower=message.lower().strip()

    for pattern in patterns:
        match=re.search(pattern,message_lower)
        if match:
            destination=match.group(1).strip().rstrip("?.!, ")
            if destination:return destination

    return None

@app.route("/plan",methods=["POST"])
def plan():
    destination=request.form.get("destination","").strip()
    start_location=request.form.get("start_location","").strip()

    try:days=int(request.form.get("days",3))
    except:days=3

    try:people=int(request.form.get("people",2))
    except:people=2

    try:budget=float(request.form.get("budget",15000))
    except:budget=15000

    interests=request.form.getlist("interests")
    days=max(1,min(days,30))
    people=max(1,min(people,50))

    try:
        destination_location=geocode_location(destination)

        if not destination_location:
            return """
            <h2>Destination not found.</h2>
            <p>Please enter a valid city, state, country or destination.</p>
            <a href="/planner">Go Back</a>
            """

        start_for_route=destination_location
        start_coordinates=None

        if start_location:
            start_coordinates=geocode_location(start_location)
            if start_coordinates:start_for_route=start_coordinates

        places_data=get_places(destination_location["lat"],destination_location["lon"])

        for place in places_data:
            place["tags"]=classify_place(place)
            place["description"]=create_description(place)
            place["ai_score"]=calculate_ai_score(place,interests)

        places_data.sort(key=lambda x:x["ai_score"],reverse=True)

        itinerary=create_full_itinerary(places_data,days,start_for_route)
        weather=get_weather(destination_location["lat"],destination_location["lon"])

        transport_distance=None

        if start_coordinates:
            transport_distance=haversine(
                start_coordinates["lat"],start_coordinates["lon"],
                destination_location["lat"],destination_location["lon"]
            )

        transport_options=create_transport_options(
            start_location,destination,transport_distance
        )

        budget_per_person=round(budget/people,2)
        session.pop("chat_history",None)

        return render_template(
            "result.html",
            destination=destination,
            location=destination_location,
            start_location=start_location,
            places=places_data,
            itinerary=itinerary,
            weather=weather,
            days=days,
            people=people,
            budget=budget,
            budget_per_person=budget_per_person,
            interests=interests,
            transport_options=transport_options
        )

    except Exception as error:
        print("PLAN ERROR:",error)
        return f"""
        <h2>Something went wrong.</h2>
        <p>{error}</p>
        <a href="/planner">Go Back</a>
        """

@app.route("/chat",methods=["POST"])
def chat():
    data=request.get_json(silent=True) or {}
    message=data.get("message","").strip()

    if not message:
        return jsonify({"reply":"Please type something.","type":"text"})

    destination=extract_destination(message)

    if destination:
        try:
            location=geocode_location(destination)

            if location:
                places_data=get_places(location["lat"],location["lon"])

                for place in places_data:
                    place["tags"]=classify_place(place)
                    place["description"]=create_description(place)
                    place["ai_score"]=calculate_ai_score(place,[])

                places_data.sort(key=lambda x:x["ai_score"],reverse=True)

                return jsonify({
                    "reply":f"🌍 I found these real places around {destination.title()} using live destination data:",
                    "type":"destination",
                    "places":places_data[:10]
                })

        except Exception as error:
            print("Destination search error:",error)

    return jsonify({"reply":ask_gemini(message),"type":"text"})

@app.route("/clear-chat",methods=["POST"])
def clear_chat():
    session.pop("chat_history",None)
    return jsonify({"success":True})

if __name__=="__main__":
    app.run(debug=True)
