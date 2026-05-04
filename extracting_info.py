import json


def find_dist_time(payload: str):
    dist_time_idx = payload.find("\u2022")
    lower_bound = upper_bound = dist_time_idx
    lower_found = upper_found = False
    while not (lower_found and upper_found):
        if not lower_found:
            lower_bound -= 1
            if payload[lower_bound] == ">":
                lower_found = True
                lower_bound +=1

        if not upper_found:
            upper_bound += 1
            if payload[upper_bound] == "<":
                upper_found = True
    
    l = payload[lower_bound : upper_bound].split("\u2022")
    distance = l[0].strip()
    duration = l[1].strip()

    return {
        "distance (km)": float(distance[:-3]),
        "duration (mins)": float(duration[:-5])
    }

def find_money_based_on_thb_symbol(payload: str):
    # Assuming there is a text "...\u0e3f %f<..."
    money_idx = payload.find("\u0e3f") # find baht symbol
    upper_bound = money_idx
    upper_found = False
    while not (upper_found):
        if not upper_found:
            upper_bound += 1
            if payload[upper_bound] == "<":
                upper_found = True
    
    money = payload[money_idx+1 : upper_bound].strip()
    return {
        "money (\u0e3f)": float(money)
    }


def find_money_based_on_thb_text(payload: str):
    # Assuming there is a text "...THB %f<..."
    money_idx = payload.find("THB") # find baht symbol
    upper_bound = money_idx
    upper_found = False
    while not (upper_found):
        if not upper_found:
            upper_bound += 1
            if payload[upper_bound] == "<":
                upper_found = True
    money = payload[money_idx+4 : upper_bound].strip()
    return {
        "money (\u0e3f)": float(money)
    }


def find_grabtaxi_subtype(payload: str):
    if payload.find("Standard Bike") >= 0:
        subtype = "Standard Bike"
    elif payload.find("Saver Bike") >= 0:
        subtype = "Saver Bike"
    else:
        subtype = None
    return {
        "subtype": subtype
    }

def main():
    MESSAGE_FILE = "data/messages.json"
    EXTRACTED_INFO_FILE = "data/extracted_info.json"

    with open(MESSAGE_FILE) as f:
        messages = json.load(f)

    processed_infos = []
    for idx, message in enumerate(messages):
        # dt = datetime.fromtimestamp(float(message["date"][:-3]))
        payload:str = message["payload"][0]
        try:
            if payload.find("GrabFood") >= 0:
                money = find_money_based_on_thb_symbol(payload)
                info = {
                    "type": "GrabFood",
                    **money
                }
            elif payload.find("Grabtaxi") >= 0:
                distance_time = find_dist_time(payload)
                money = find_money_based_on_thb_symbol(payload)
                subtype = find_grabtaxi_subtype(payload)                
                info = {
                    "type": "GrabTaxi",
                    **subtype,
                    **distance_time,
                    **money
                }
            elif payload.find("JustGrab") >= 0:
                distance_time = find_dist_time(payload)
                money = find_money_based_on_thb_text(payload)

                info = {
                    "type": "JustGrab",
                    **distance_time,
                    **money
                }
            elif payload.find("GrabBike Saver") >= 0:
                distance_time = find_dist_time(payload)
                money = find_money_based_on_thb_text(payload)     
                info = {
                    "type": "GrabBike Saver",
                    **distance_time,
                    **money
                }
            else:
                info = {
                    "type": "None",
                }

            processed_infos.append({
                "idx": idx,
                "ts": float(message["date"][:-3]), 
                **info
            })
        except Exception as e:
            print(f"idx {idx} has some problem")
            print(e)
            processed_infos.append({
                "idx": idx,
                "ts": float(message["date"][:-3]), 
                "type": "Error",
                "desc": str(e)
            })
    # print(processed_infos)
    with open(EXTRACTED_INFO_FILE, "w") as f:
        json.dump(processed_infos, f)
        

if __name__ == "__main__":
    main()