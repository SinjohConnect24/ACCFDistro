import middleware.ACWC24.acwc24 as middleware
import os
import random
import requests
from datetime import datetime
import calendar
import pathlib
import logging
import http.client as httplib

# Debug logging
httplib.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
req_log = logging.getLogger("requests.packages.urllib3")
req_log.setLevel(logging.DEBUG)
req_log.propagate = True


def runner(
    webhook_url,
    region_letter,
    webhook_prefix,
    whook_bool,
    push_bool,
    srv_dir,
    region_code,
):

    # Get current path of python script
    current_path = os.path.split(os.path.abspath(__file__))[0]

    # Now we get a random BRRES file.
    brres_to_encode = random.choice(os.listdir(f"{current_path}/items"))

    # Now we strip it of the path and extension.
    head_tail = pathlib.Path(brres_to_encode).stem

    # From that, we get the path of the JSON file.
    json_path = f"{current_path}/src/{head_tail}.json"

    # At this point in time, we have our JSON and BRRES pair.
    # It's time to encode it with ACWC24, so as to speak and/or say.

    middleware.create(head_tail, False)

    # First, we properly name it.
    os.rename(
        f"{current_path}/build/{head_tail}_{region_letter}.arc",
        f"{current_path}/build/rvforest_{region_code}.dat",
    )
    # Then, we do a quick check here.
    if push_bool == True:
        # If it's good, then we send it.
        os.replace(
            f"{current_path}/build/rvforest_{region_code}.dat",
            f"{srv_dir}/ruu/rvforest_{region_code}.dat",
        )
    else:
        print("[INFO] PUSH_BOOL IS DISABLED.")

    if whook_bool == True:
        data = {
            "username": "Animal Crossing DLC Bot",
            "avatar_url": "https://cdn2.steamgriddb.com/icon_thumb/f4d4c95a4336cebe07df62e614f602f5.png",
            "content": "We are now serving a new DLC item!",
            "embeds": [
                {
                    "author": {
                        "name": "SophiaDev's ACCF Distribution System",
                        "icon_url": "https://cdn-icons-png.flaticon.com/512/6612/6612622.png",
                    },
                    "title": "New DLC Item!",
                    "description": f"We are now serving {head_tail}",
                    "color": 11342935,
                    "fields": [
                        {
                            "name": "Distribution time:",
                            "value": int(calendar.timegm(datetime.utcnow().timetuple())),
                            "inline": True
                        },
                        {
                            "name": "Debug data",
                            "value": f"{region_letter}/{region_code}",
                            "inline": True
                        }
                    ],
                    "thumbnail": {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7c/Animal_Crossing_Leaf.svg/2149px-Animal_Crossing_Leaf.svg.png"
                    },
                    "image": {
                        "url": "https://static0.gamerantimages.com/wordpress/wp-content/uploads/2020/05/Animal-Crossing-New-Horizons-Able-Sisters-Exterior-Butterfly-Dress.jpg"
                    },
                    "footer": {
                        "text": "Enjoy!",
                        "icon_url": "https://b.thumbs.redditmedia.com/-KjPTWzzbWcj-lNo9uFShd7B-UJs6ptZ375LfHyKoPI.png",
                    },
                }
            ],
        }
        post_webhook = requests.post(
            f"{webhook_prefix}://{webhook_url}", json=data, allow_redirects=True
        )
    else:
        print("[INFO] WHOOK_BOOL is disabled.")

    # Our work here is done. We clean up a bit and return 0.
    for item in ["E", "J", "K", "P"]:
        if os.path.exists(f"{current_path}/build/{head_tail}_{item}.arc"):
            os.remove(f"{current_path}/build/{head_tail}_{item}.arc")
    return 0
