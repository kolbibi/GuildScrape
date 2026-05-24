from urllib.request import urlopen, Request
import json
import time
import csv
import sys
from datetime import datetime, timezone
import os

from dotenv import load_dotenv
load_dotenv()

def main():
    start_day = "2026-03-01T00:00:00.000000Z"

    if len(sys.argv) > 1:
        start_day = sys.argv[1]
    output_file = "./dataCollection.csv"
    # import os
    guild_name = "Godly"
    start_url = "https://api.wynncraft.com/v3/"
    player_url = start_url + "player/"
    guild_url = start_url + "guild/"
    weekly_csv_file = "./weekly_data.csv"
    monthly_csv_file = "./monthly_data.csv"
    api_token = os.environ.get("API_TOKEN")
    class Response:
        def __init__(self, text, status_code, headers):
            self.text = text
            self.status_code = status_code
            self.headers = headers
        def json(self):
            return json.loads(self.text)
    class Requests():
        def __init__(self):
            self.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/116.0.5845.97 Safari/537.36",
                "Authorization": f"Bearer {api_token}"
            }
        def get(self, url):
            req = Request(url, headers=self.headers)
            with urlopen(req) as response:
                data = response.read()
                encoding = response.info().get_content_charset("utf-8")
                text = data.decode(encoding)
                return Response(text, response.getcode(), dict(response.info()))
    requests = Requests()
    tomes = {}
    guild_req = requests.get(guild_url + guild_name)
    guild_data = guild_req.json()

    # print(guild_data["members"])
    all_members = []
    guild_break_username = {}
    guild_break_down = {}
    for key in guild_data['members'].keys():
        if key =="total":
            continue
        guild_break_down[key] = []
        guild_break_username[key] = []
        for member in guild_data['members'][key]:
            guild_break_username[key].append(member)
            if guild_data['members'][key][member].get('weekly', False) and guild_data['members'][key][member]['weekly']['completed'] and guild_data['members'][key][member]['weekly']['streak']%5==0:
                tomes[member] = guild_data['members'][key][member]['weekly']
            guild_break_down[key].append(guild_data['members'][key][member]['uuid'])
            all_members.append(guild_data['members'][key][member]['uuid'])
    member_stats = {}
    for member in all_members:
        member_data = json.loads(json.dumps(requests.get(player_url + member).json(), default=str))
        
        member_stats[member.lower()] = member_data
        time.sleep(2)
    incognito = []
    for member in sorted(member_stats.keys()):
        if not member_stats[member]['restrictions']['mainAccess'] and not member_stats[member]['restrictions']['onlineStatus']:
            # print(f"{member}: {member_stats[member]["playtime"]} {member_stats[member]["restrictions"]}")
            # print(f"{member_stats[member]['username']}: {member_stats[member]['restrictions']}")
            pass
        else:
            # print(f"{member} icognito")
            incognito.append(member)
    # member_stats = {k: v for k,v in member_stats.items() if k not in incognito}
    headers = ["date", "uuid", "rank", "username", "lastJoined", "daysLastJoined", "playtime", "wars",  "graids", "lootruns", "raids", "totalLevel", "contentCompletion"]
    time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    guild_members = []
    # file_exists = os.path.isfile(output_file)
    # file_has_content = file_exists and os.path.getsize(output_file) > 0
    now_utc = datetime.now(timezone.utc)

    formatted = now_utc.strftime(time_format)
    with open(output_file, "a", newline="") as f:
        writer = csv.writer(f)
        if f.tell()==0:
            writer.writerow(headers)
        
        for uuid in member_stats:
            if uuid in incognito:
                continue
            member = member_stats[uuid]
            guild_members.append(member['username'])
            # print(member['globalData']['guildRaids'])
            # print(member['globalData']['raids'])
            # print([member['globalData']['guildRaids'][raid] for raid in member['globalData']['guildRaids']])
            days_last_joined =  now_utc - datetime.strptime((member.get('lastJoin') or "1959-05-03T21:47:01.317000Z"), time_format).replace(tzinfo=timezone.utc)
            stats = [formatted, uuid, (member.get('guild') or {'rank': 'RECRUIT'})['rank'],member["username"], (member.get('lastJoin') or "1959-05-03T21:47:01.317000Z"), 
                    round(days_last_joined.total_seconds()/60/60/24, 3) ,member['playtime'], member['globalData']["wars"], member['globalData']['guildRaids']['total'],
                    member['globalData']['lootruns'], member['globalData']["raids"]['total'], member["globalData"]['totalLevel'], member['globalData']['contentCompletion']]
            # print(stats)
            writer.writerow(stats)
    player_data = {}
    weekly_data = {}
    no_weekly_data = []
    monthly_data = {}
    no_monthly_data = []
    def subtract_date_string(day1, day2):
        filter1 = datetime.strptime(day1, time_format)
        filter2 = datetime.strptime(day2, time_format)
        days_time = filter1 - filter2
        return round(abs(days_time.total_seconds()/60/60/24), 3)

    with open(output_file, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uuid = row['uuid']
            if uuid not in player_data:
                player_data[uuid] = []
            if len(player_data[uuid]) >= 5:
                player_data[uuid] = player_data[uuid][-4:] + [row]
            else:
                player_data[uuid].append(row)


    for player in player_data:
        #  player_data[player]
        
        dates = [day['date'] for day in player_data[player]]
        # if dates[-1]==formatted:
        # if player_data[player][-1]['username']=="StyNath":
        #         print(player_data[player][-1]['username'])
        #         print(dates)
        #         print(round(subtract_date_string(dates[-1], dates[-2]), 0))
        #         print(formatted)
        #         print(len(player_data[player]) > 1 and dates[-1]==formatted and round(subtract_date_string(dates[-1], dates[-2]), 0)==7)
        # formatted = "2026-03-08T00:00:23.653376Z"
        # print(json.dumps(player_data[player], 2))
        
        if len(player_data[player]) > 1 and dates[-1]==formatted and 4<= round(subtract_date_string(dates[-1], dates[-2]), 0) <= 10:
            # print(f"Got to weekly: {player_data[player][-1]['username']}")
           
            weekly_data[player] = {
                "date": formatted,
                "username": player_data[player][-1]['username'], 
                "uuid": player,
                "rank": player_data[player][-1]['rank'],
                "daysLastJoined": round(float(player_data[player][-1]["daysLastJoined"]), 2),
                "playtime": round(float(player_data[player][-1]['playtime']) -float(player_data[player][-2]['playtime']), 2),
                "wars":round(float(player_data[player][-1]['wars']) -float(player_data[player][-2]['wars']),2 ),
                "graids": round(float(player_data[player][-1]['graids']) -float(player_data[player][-2]['graids']), 2),
                "lootruns": round(float(player_data[player][-1]['lootruns']) -float(player_data[player][-2]['lootruns']), 2),
                "raids": round(float(player_data[player][-1]['raids']) -float(player_data[player][-2]['raids']), 2),
                "totalLevel":round(float(player_data[player][-1]['totalLevel']) -float(player_data[player][-2]['totalLevel']), 2),
                "contentCompletion":round(float(player_data[player][-1]['contentCompletion']) -float(player_data[player][-2]['contentCompletion']), 2),
                "lastJoined": player_data[player][-1]['lastJoined']
                                }
            # print(weekly_data)
        else:
            no_weekly_data.append(player)
        this_month = [round(subtract_date_string(formatted, d), 0)<=31 for d in dates]
        oldest_this_month = 0
        for i in this_month:
            if i:
                oldest_this_month += 1
        

        if "StyNath" ==player_data[player][-1]['username']:
            # print(len(player_data[player]) > 2 and sum(this_month) > 1 and round(subtract_date_string(start_day, formatted),0)%28==0)
            # print(round(subtract_date_string(start_day, formatted),0)%28==0)
            # print(round(subtract_date_string(start_day, formatted),0))
            print(f"oldest_this_month_div: {round(subtract_date_string(dates[-oldest_this_month], formatted),0)}")
            print(f"start_day_to_today_formatted: {round(subtract_date_string(start_day, formatted),0)}")
        # 25 <= round(subtract_date_string(dates[-oldest_this_month], formatted),0) <= 31 
        if len(player_data[player]) > 1 and abs(round(subtract_date_string(start_day, formatted),0))%28 <= 3:
            month_stats = {
                "date": formatted,
                "username": player_data[player][-1]['username'], 
                "uuid": player,
                "rank": player_data[player][-1]['rank'],
                "daysLastJoined": round(float(player_data[player][-1]["daysLastJoined"]), 2),
                "playtime":round(float(player_data[player][-1]['playtime']) -float(player_data[player][-oldest_this_month]['playtime']), 2),
                "wars":round(float(player_data[player][-1]['wars']) -float(player_data[player][-oldest_this_month]['wars']), 2),
                "graids":round(float(player_data[player][-1]['graids']) -float(player_data[player][-oldest_this_month]['graids']), 2),
                "lootruns": round(float(player_data[player][-1]['lootruns']) -float(player_data[player][-oldest_this_month]['lootruns']), 2),
                "raids":round(float(player_data[player][-1]['raids']) -float(player_data[player][-oldest_this_month]['raids']), 2),
                "totalLevel":round(float(player_data[player][-1]['totalLevel']) -float(player_data[player][-oldest_this_month]['totalLevel']), 2),
                "contentCompletion":round(float(player_data[player][-1]['contentCompletion']) -float(player_data[player][-oldest_this_month]['contentCompletion']), 2),
                "lastJoined": player_data[player][-1]['lastJoined']
            }
            monthly_data[player] = month_stats
            # if player_data[player][-1]['username']=="StyNath":
            #     print(json.dumps(player_data[player], indent=2))

    # Write CSV
    fieldnames = [
        "date",
        "username",
        "uuid",
        "rank",
        "daysLastJoined",
        "playtime",
        "wars",
        "graids",
        "lootruns",
        "raids",
        "totalLevel",
        "contentCompletion",
        "lastJoined"
    ]
    with open(weekly_csv_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if f.tell()==0:
            writer.writeheader()
        
        # Write each player's monthly data
        for player, data in weekly_data.items():
            writer.writerow(data)

    # Write CSV
    with open(monthly_csv_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if f.tell()==0:
            writer.writeheader()
        
        # Write each player's monthly data
        for player, data in monthly_data.items():
            writer.writerow(data)
    from collections import defaultdict
    import plotly.graph_objects as go

    numeric_fields = ["playtime", "wars", "graids", "lootruns", "raids", "totalLevel", "contentCompletion", "daysLastJoined"]

    data = defaultdict(lambda: defaultdict(list))

    # Read CSV
    with open(weekly_csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["uuid"]
            timestamp = row["date"]
            username = row.get("username", key)
            for field in numeric_fields:
                if row.get(field):  # only add if value exists
                    data[key][field].append({"timestamp": timestamp, "value": float(row[field]), "username": username})

    fig = go.Figure()
    traces = []
    trace_info = []

    # Add traces only if there is data
    for key in data:
        for field in numeric_fields:
            if data[key][field]:  # skip empty fields
                trace = go.Scatter(
                    x=[entry["timestamp"] for entry in data[key][field]],
                    y=[entry["value"] for entry in data[key][field]],
                    mode="lines+markers",
                    name=f"{data[key][field][-1]['username']} - {field}",
                    visible=False
                )
                fig.add_trace(trace)
                trace_info.append((key, field))

    # Player dropdown
    player_buttons = []
    player_keys = list(data.keys())

    for key in player_keys:
        visibility = [False] * len(fig.data)
        for j, (k, f) in enumerate(trace_info):
            if k == key:
                visibility[j] = True
        # Pick first non-empty field to get username
        first_field = next((f for f in numeric_fields if data[key][f]), None)
        username = data[key][first_field][-1]['username'] if first_field else key
        player_buttons.append(dict(
            label=username,
            method="update",
            args=[{"visible": visibility},
                {"title": f"Player: {username}"}]
        ))

    # Field dropdown
    field_buttons = []
    for field in numeric_fields:
        visibility = [False] * len(fig.data)
        for j, (k, f) in enumerate(trace_info):
            if f == field:
                visibility[j] = True
        field_buttons.append(dict(
            label=field,
            method="update",
            args=[{"visible": visibility},
                {"title": f"Field: {field}"}]
        ))

    fig.update_layout(
        updatemenus=[
            dict(active=0, buttons=player_buttons, x=0, y=1.1, xanchor='left', direction='down'),
            dict(active=0, buttons=field_buttons, x=0.3, y=1.1, xanchor='left', direction='down')
        ],
        title="Interactive Player Stats"
    )

    weekly_html_str = fig.to_html(
        include_plotlyjs="cdn",
        full_html=False
    )


    data = defaultdict(lambda: defaultdict(list))

    # Read CSV
    with open(monthly_csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["uuid"]
            timestamp = row["date"]
            username = row.get("username", key)
            for field in numeric_fields:
                if row.get(field):  # only add if value exists
                    data[key][field].append({"timestamp": timestamp, "value": float(row[field]), "username": username})

    fig = go.Figure()
    traces = []
    trace_info = []

    # Add traces only if there is data
    for key in data:
        for field in numeric_fields:
            if data[key][field]:  # skip empty fields
                trace = go.Scatter(
                    x=[entry["timestamp"] for entry in data[key][field]],
                    y=[entry["value"] for entry in data[key][field]],
                    mode="lines+markers",
                    name=f"{data[key][field][-1]['username']} - {field}",
                    visible=False
                )
                fig.add_trace(trace)
                trace_info.append((key, field))

    # Player dropdown
    player_buttons = []
    player_keys = list(data.keys())

    for key in player_keys:
        visibility = [False] * len(fig.data)
        for j, (k, f) in enumerate(trace_info):
            if k == key:
                visibility[j] = True
        # Pick first non-empty field to get username
        first_field = next((f for f in numeric_fields if data[key][f]), None)
        username = data[key][first_field][-1]['username'] if first_field else key
        player_buttons.append(dict(
            label=username,
            method="update",
            args=[{"visible": visibility},
                {"title": f"Player: {username}"}]
        ))

    # Field dropdown
    field_buttons = []
    for field in numeric_fields:
        visibility = [False] * len(fig.data)
        for j, (k, f) in enumerate(trace_info):
            if f == field:
                visibility[j] = True
        field_buttons.append(dict(
            label=field,
            method="update",
            args=[{"visible": visibility},
                {"title": f"Field: {field}"}]
        ))

    fig.update_layout(
        updatemenus=[
            dict(active=0, buttons=player_buttons, x=0, y=1.1, xanchor='left', direction='down'),
            dict(active=0, buttons=field_buttons, x=0.3, y=1.1, xanchor='left', direction='down')
        ],
        title="Interactive Player Stats"
    )

    monthly_html_str = fig.to_html(
        include_plotlyjs="cdn",
        full_html=False
    )
    rows = []
    if not monthly_data:
        with open(monthly_csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        if len(rows) > 0:
            # Step 2: Find latest date
            latest_date = max(row["date"] for row in rows)

            # Step 3: Build weekly_data from rows matching latest_date
            for row in rows:
                if row["date"] == latest_date:
                    player = row["uuid"]
                    monthly_data[player] = {
                        "date": row["date"],
                        "username": row["username"],
                        "uuid": player,
                        "rank": row["rank"],
                        "daysLastJoined": float(row["daysLastJoined"]),
                        "playtime": float(row["playtime"]),
                        "wars": float(row["wars"]),
                        "graids": float(row["graids"]),
                        "lootruns": float(row["lootruns"]),
                        "raids": float(row["raids"]),
                        "totalLevel": float(row["totalLevel"]),
                        "contentCompletion": float(row["contentCompletion"]),
                        "lastJoined": row["lastJoined"]
                    }
    from collections import defaultdict
    import plotly.graph_objects as go


    data = defaultdict(lambda: defaultdict(list))

    # Read CSV
    with open(weekly_csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["uuid"]
            timestamp = row["date"]
            username = row.get("username", key)
            for field in numeric_fields:
                if row.get(field):  # only add if value exists
                    data[key][field].append({"timestamp": timestamp, "value": float(row[field]), "username": username})

    fig = go.Figure()
    traces = []
    trace_info = []

    # Add traces only if there is data
    for key in data:
        for field in numeric_fields:
            if data[key][field]:  # skip empty fields
                trace = go.Scatter(
                    x=[entry["timestamp"] for entry in data[key][field]],
                    y=[entry["value"] for entry in data[key][field]],
                    mode="lines+markers",
                    name=f"{data[key][field][-1]['username']} - {field}",
                    visible=False
                )
                fig.add_trace(trace)
                trace_info.append((key, field))

    # Player dropdown
    player_buttons = []
    player_keys = list(data.keys())

    for key in player_keys:
        visibility = [False] * len(fig.data)
        for j, (k, f) in enumerate(trace_info):
            if k == key:
                visibility[j] = True
        # Pick first non-empty field to get username
        first_field = next((f for f in numeric_fields if data[key][f]), None)
        username = data[key][first_field][-1]['username'] if first_field else key
        player_buttons.append(dict(
            label=username,
            method="update",
            args=[{"visible": visibility},
                {"title": f"Player: {username}"}]
        ))

    # Field dropdown
    field_buttons = []
    for field in numeric_fields:
        visibility = [False] * len(fig.data)
        for j, (k, f) in enumerate(trace_info):
            if f == field:
                visibility[j] = True
        field_buttons.append(dict(
            label=field,
            method="update",
            args=[{"visible": visibility},
                {"title": f"Field: {field}"}]
        ))

    fig.update_layout(
        updatemenus=[
            dict(active=0, buttons=player_buttons, x=0, y=1.1, xanchor='left', direction='down'),
            dict(active=0, buttons=field_buttons, x=0.3, y=1.1, xanchor='left', direction='down')
        ],
        title="Interactive Player Stats"
    )

    weekly_html_str = fig.to_html(
        include_plotlyjs="cdn",
        full_html=False
    )

    data = defaultdict(lambda: defaultdict(list))

    # Read CSV
    with open(monthly_csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["uuid"]
            timestamp = row["date"]
            username = row.get("username", key)
            for field in numeric_fields:
                if row.get(field):  # only add if value exists
                    data[key][field].append({"timestamp": timestamp, "value": float(row[field]), "username": username})

    fig = go.Figure()
    traces = []
    trace_info = []

    # Add traces only if there is data
    for key in data:
        for field in numeric_fields:
            if data[key][field]:  # skip empty fields
                trace = go.Scatter(
                    x=[entry["timestamp"] for entry in data[key][field]],
                    y=[entry["value"] for entry in data[key][field]],
                    mode="lines+markers",
                    name=f"{data[key][field][-1]['username']} - {field}",
                    visible=False
                )
                fig.add_trace(trace)
                trace_info.append((key, field))

    # Player dropdown
    player_buttons = []
    player_keys = list(data.keys())

    for key in player_keys:
        visibility = [False] * len(fig.data)
        for j, (k, f) in enumerate(trace_info):
            if k == key:
                visibility[j] = True
        # Pick first non-empty field to get username
        first_field = next((f for f in numeric_fields if data[key][f]), None)
        username = data[key][first_field][-1]['username'] if first_field else key
        player_buttons.append(dict(
            label=username,
            method="update",
            args=[{"visible": visibility},
                {"title": f"Player: {username}"}]
        ))

    # Field dropdown
    field_buttons = []
    for field in numeric_fields:
        visibility = [False] * len(fig.data)
        for j, (k, f) in enumerate(trace_info):
            if f == field:
                visibility[j] = True
        field_buttons.append(dict(
            label=field,
            method="update",
            args=[{"visible": visibility},
                {"title": f"Field: {field}"}]
        ))

    fig.update_layout(
        updatemenus=[
            dict(active=0, buttons=player_buttons, x=0, y=1.1, xanchor='left', direction='down'),
            dict(active=0, buttons=field_buttons, x=0.3, y=1.1, xanchor='left', direction='down')
        ],
        title="Interactive Player Stats"
    )

    monthly_html_str = fig.to_html(
        include_plotlyjs="cdn",
        full_html=False
    )
    import html

    def make_table(pairs, value_label):
        i = 0
        rows = []
        for k, v, rank in pairs:
            is_exempt = rank.lower() in ('chief', 'owner')
            if not is_exempt:
                i += 1
            position = 'N/A' if is_exempt else i
            adjusted_v = round(v, 2)
            rows.append(
                f"<tr><td>{position}</td><td>{html.escape(str(k))}</td><td>{html.escape(str(adjusted_v))}</td><td>{html.escape(str(rank))}</td></tr>"
            )
        rows = "\n".join(rows)
        return f"""
<table border="1" style="border-collapse: collapse; font-size: 14px;">
    <tr>
        <th>#</th>
        <th>Username</th>
        <th>{html.escape(str(value_label))}</th>
        <th>Rank</th>
    </tr>
{rows}
</table>
"""
    def weeklies_table(tomes):
        i = 0
        rows = []
        for player in tomes.keys():
            
            i += 1
            position = i
            rows.append(
                f"<tr><td>{position}</td><td>{html.escape(player)}</td><td>{html.escape(str(tomes[player]['streak']))}</td></tr>"
            )
        rows = "\n".join(rows)
        return f"""
<table border="1" style="border-collapse: collapse; font-size: 14px;">
    <tr>
        <th>#</th>
        <th>Username</th>
        <th>{html.escape(str("Weeklies"))}</th>
    </tr>
{rows}
</table>
"""


    def full_field_dropdown(field, asc_weekly, asc_monthly, desc_weekly, desc_monthly):
        return f"""
        <details style="margin-bottom: 30px;">
            <summary style="font-size: 20px; font-weight: bold; cursor: pointer;">
                {html.escape(field)}
            </summary>

            <div style="
                margin-top: 15px;
                display: flex;
                gap: 25px;
                flex-wrap: nowrap;
            ">

                <div>
                    <h4>Top Weekly</h4>
                    {make_table(asc_weekly, field)}
                </div>

                <div>
                    <h4>Top Monthly</h4>
                    {make_table(asc_monthly, field)}
                </div>

                <div>
                    <h4>Lowest Weekly</h4>
                    {make_table(desc_weekly, field)}
                </div>

                <div>
                    <h4>Lowest Monthly</h4>
                    {make_table(desc_monthly, field)}
                </div>

            </div>
        </details>
        """
    def graid_make_table(pairs, value_label):
        i = 0
        rows = []
        for k, v, rank in pairs:
            is_exempt = rank.lower() in ('chief', 'owner')
            if not is_exempt:
                i += 1
            position = 'N/A' if is_exempt else i
            
            rows.append(
                f"<tr><td>{position}</td><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td><td>{html.escape(str(rank))}</td><td>{v*512//(64*64)}</td></tr>"
            )
        rows = "\n".join(rows)
        return f"""
<table border="1" style="border-collapse: collapse; font-size: 14px;">
    <tr>
        <th>#</th>
        <th>Username</th>
        <th>{html.escape(str(value_label))}</th>
        <th>Rank</th>
        <th>LE Generated</th>
    </tr>
{rows}
</table>
"""


    def graid_full_field_dropdown(field, asc_weekly, asc_monthly, desc_weekly, desc_monthly):
        return f"""
        <details style="margin-bottom: 30px;">
            <summary style="font-size: 20px; font-weight: bold; cursor: pointer;">
                {html.escape(field)}
            </summary>

            <div style="
                margin-top: 15px;
                display: flex;
                gap: 25px;
                flex-wrap: nowrap;
            ">

                <div>
                    <h4>Top Weekly</h4>
                    {graid_make_table(asc_weekly, field)}
                </div>

                <div>
                    <h4>Top Monthly</h4>
                    {graid_make_table(asc_monthly, field)}
                </div>

                <div>
                    <h4>Lowest Weekly</h4>
                    {graid_make_table(desc_weekly, field)}
                </div>

                <div>
                    <h4>Lowest Monthly</h4>
                    {graid_make_table(desc_monthly, field)}
                </div>

            </div>
        </details>
        """

    all_tables_html = ""
    # money_made_for_guild_weekly_tables = ""
    # money_made_for_guild_weekly = sorted([(weekly_data[uuid]["username"], (3 * weekly_data[uuid]["graids"] + weekly_data[uuid]["wars"])/4) for uuid in weekly_data], key=lambda x: x[1], reverse=True)
    # # money_made_for_guild_monthly_tables = ""
    # money_made_for_guild_monthly = sorted([(monthly_data[uuid]["username"], (3 * monthly_data[uuid]["graids"] + monthly_data[uuid]["wars"])/4) for uuid in monthly_data], key=lambda x: x[1], reverse=True)
    for field in numeric_fields:
        asc_weekly = sorted([(weekly_data[uuid]["username"], weekly_data[uuid][field], weekly_data[uuid]['rank']) for uuid in weekly_data], key=lambda x: x[1], reverse=True)
        asc_monthly = sorted([(monthly_data[uuid]["username"], monthly_data[uuid][field], monthly_data[uuid]['rank']) for uuid in monthly_data], key=lambda x: x[1], reverse=True)
        desc_weekly = sorted([(weekly_data[uuid]["username"], weekly_data[uuid][field], weekly_data[uuid]['rank']) for uuid in weekly_data], key=lambda x: x[1], reverse=False)
        desc_monthly = sorted([(monthly_data[uuid]["username"], monthly_data[uuid][field], monthly_data[uuid]['rank']) for uuid in monthly_data], key=lambda x: x[1], reverse=False)
        if field == "graids":
            all_tables_html += graid_full_field_dropdown(field, 
                asc_weekly[:30],
                asc_monthly[:30],
                desc_weekly[:30],
                desc_monthly[:30]
                )
        else:
            all_tables_html += full_field_dropdown(
                field,
                asc_weekly[:30],
                asc_monthly[:30],
                desc_weekly[:30],
                desc_monthly[:30]
            )
    if not monthly_data:
        month_date = "Not yet collected"
    else:
        month_date = monthly_data[player]["date"]
    html_ = f"""
    <html>
    <head>
    <title>GuildScrape</title>
    </head>
    <body>
    <h1>Performance Rankings</h1>
    <p><strong>**Chiefs and Owner not eligible for rewards**</strong></p>
    <p>Warning icognito players: {[member_stats[uuid]['username'] for uuid in incognito]}</p>
    <br/>
    <p>** Monthly data last collected: {month_date} Year/Month/Day/H/M/S format</p>
    <p>** Weekly data collected last collected: {formatted} Year/Month/Day/H/M/S format</p>
    <h2>Weekly's Tome Winners</h2>
    {weeklies_table(tomes, )}
    {all_tables_html}
    <div style="display: flex; flex-direction: row">
        <h1 style="width: 50%">Weekly Graphs</h1>
        <h1>Monthly Graphs</h1>
    </div>
    <div style="display: flex; flex-direction: row">
        <div style="width: 50%">
        {weekly_html_str}
        </div>
        <div style="width: 50%">
        {monthly_html_str}
        </div>
    </div>
    </body>
    </html>
    """
    with open("index.html", "w") as f:
        f.write(html_)
if __name__ == "__main__":
    main()
