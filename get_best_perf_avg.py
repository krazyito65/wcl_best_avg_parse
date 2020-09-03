import requests
import json
import re
import pprint

pp = pprint.PrettyPrinter(indent=2)

classesDict = {
    "death knight": {"blood": "tank", "frost": "dps", "unholy": "dps"},
    "demon hunter": {"havoc": "dps", "vengeance": "tank"},
    "druid": {
        "balance": "dps",
        "feral": "dps",
        "guardian": "tank",
        "restoration": "healer",
    },
    "hunter": {"beast mastery": "dps", "marksmanship": "dps", "survival": "dps"},
    "mage": {"arcane": "dps", "fire": "dps", "frost": "dps"},
    "monk": {"brewmaster": "tank", "mistweaver": "healer", "windwalker": "dps"},
    "paladin": {"holy": "healer", "protection": "tank", "retribution": "dps"},
    "priest": {"discipline": "healer", "holy": "healer", "shadow": "healer"},
    "rogue": {"assassination": "dps", "outlaw": "dps", "subtlety": "dps"},
    "shaman": {"elemental": "dps", "enhancement": "dps", "restoration": "healer"},
    "warlock": {"affliction": "dps", "demonology": "dps", "destruction": "dps"},
    "warrior": {"arms": "dps", "fury": "dps", "protection": "tank"},
}


######### Functions to parse data


def get_role_parses(character_json, player_role, metric):
    """Return a list of parses related to the player_role

    When calling the WCL API, you can provide a 'metric' to pull specific types of parses.
    For our case, it will normally be either HPS (healing) or DPS (dps/tanking)
    We do not use any other metric for tanks, since it is very subjective to the gear of the player and difficulty of content.

    character_json -- Any list of 'parses' usualyl provided by the WCL API, or curated by other functions.
    player_role -- This is the role the player signed up for via the bot.
    metric -- The metric used to obtain these parses.

    Will return a new list of 'parses' that include only the specilization that the metric is used for.
    Will return empty list if no parses are found for that metric.
    """

    parses = []

    for parse in character_json:
        spec = parse["spec"].lower()
        player_class = parse["class"].lower()
        role = classesDict[player_class][spec]
        if player_role == role:
            parses.append(parse)
            # print(
            #     "{encounterName}\n\t{spec}\n\t{parse}\n\t{role}".format(
            #         encounterName=parse["encounterName"],
            #         spec=spec,
            #         parse=parse["percentile"],
            #         role=role,
            #     )
            # )
    return parses


def get_best_perf_avg(parses):
    """Return a singular number, with the average of the 'best' parses per boss.

    This will take the 'best' parse given per boss encounter, and average them out.
    Ideally this will mimick the 'Best Performance Average' of a given role per metric.
    This function intends to only be used by a filtered list of parses, specific to the role the metric was used for (see get_role_parses)
    Although, this function is generic enough to take any list of parses given and provide the average of all the best parses per boss.

    parses -- A list of 'parses' provided by the WCL API.

    Will return a single number that is the average of each best parse per boss
    """

    player_parses = {}

    for parse in parses:
        boss = parse["encounterName"]
        percentile = parse["percentile"]

        # If we have not seen this boss before, init it with a 0.
        try:
            best_parse = player_parses[boss]
        except:
            best_parse = 0

        if best_parse < percentile:
            player_parses[boss] = percentile

    # Can return player_parses to show best parse per boss if needed in future.
    # pp.pprint(player_parses)

    total_bosses = len(player_parses)
    total = 0
    for boss_name in player_parses:
        total += player_parses[boss_name]

    return total / total_bosses


#########################
# After this point should be how to invoke and set up to use above functions
########################


# save a text file called 'api_key' in the root with only your api key as text.
with open("api_key", "r") as file:
    api_key = file.read().replace("\n", "")

characterName = "Spicegold"
serverName = "Illidan"
serverRegion = "US"

###################
# can use a ternary to determine useful metric
# heal = hps
# otherwise, dps
###################
role = "healer"  # arbitrary variable to make below work.
metric = "hps" if re.search("heal", role) else "dps"


## Things to note:
## This excludes 'partitions', which break up a raid tier by time based on specific events that happened, either a new patch, or nerfs
## This just means, any 'older data' is lost, unless we specify 'all' partitions, since we're only looking at the most recent.
## This has the implication that someone coming back to the game recently may not have any logs at all.
## Currently there is no way to get 'all partitions' (v2 may be better in the future)
## in practice, omitting partition should be best, but depending on circumstances, 'ALL' may be needed.
base_url = "https://www.warcraftlogs.com:443/v1/parses/character/{}/{}/{}?".format(
    characterName, serverName, serverRegion
)

if metric:
    base_url += "metric={}".format(metric)


base_url += "&api_key={}".format(api_key)
r = requests.get(url=base_url)
info = r.json()

# info should be a list item
# End setup, use functions and data
role_parses = get_role_parses(info, role, metric)
best_average = get_best_perf_avg(role_parses)
print(round(best_average, 1))

################################################################################

# print(role_parses[0])

##### only used to write to the file
character_json = json.dumps(info, indent=2)

with open("character.json", "w") as out:
    out.write(character_json)


####### character_json is a string at this point
