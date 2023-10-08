#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: joevest
"""

import os
import json
import requests
import time
from datetime import datetime
from github import Github

GITHUB_TOKEN = os.environ.get('MY_GITHUB_TOKEN')
MYTHIC_META_GITHUB_TOKEN = os.environ.get('MYTHIC_META_GITHUB_TOKEN')
api_url_base = "https://api.github.com/repos/"
agent_repos = "repos.txt"  # list of repos
mythicmeta_repos = "mythicmeta_repos.txt"
git_repo_base = "https://github.com/"

datajson = "data.json"
jsonbase = {"data": []}

stats_file = "stats.json"
with open(stats_file) as f:
    stats_data = json.load(f)

#  Walk through MythicAgents list
with open(agent_repos) as f:
    headers = {"authorization": "Bearer " + GITHUB_TOKEN,
               "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    g = Github(GITHUB_TOKEN)
    for repository in f.readlines():
        if repository == "":
            continue  # skip blanks
        else:
            # Get Category and Project from line
            value = repository.split(",")
            category = value[0].strip()
            project = value[1].strip()
            url = api_url_base + project
            # Get GitHub Repo JSON from API
            print(url)
            proj = g.get_repo(project)
            print(f"{proj.name} - {proj.description}")
            default_branch = proj.get_branch(proj.default_branch)
            latest = {
                "branch": default_branch.name,
                "commit_message": default_branch.commit.commit.message,
                "commit_date": default_branch.commit.commit.author.date,
                "icon": "",
            }
            for b in proj.get_branches():
                branch = proj.get_branch(b.name)
                if branch.commit.commit.author.date > latest["commit_date"]:
                    latest = {
                        "branch": b.name,
                        "commit_message": branch.commit.commit.message,
                        "commit_date": branch.commit.commit.author.date,
                    }
            result = requests.get(url, headers=headers)
            if result.status_code == 200:
                repo_data_json = json.loads(result.text)
                if len(latest["branch"]) > 20:
                    latest["branch"] = latest["branch"][:20] + "..."
                if len(latest["commit_message"]) > 60:
                    latest["commit_message"] = latest["commit_message"][:60] + "..."
                repo_data_json["latest"] = latest
                # Add custom category field to JSON
                repo_data_json['category'] = category
                repo_data_json["clones"] = {
                    "count": -1,
                    "uniques": -1
                }
                try:
                    clones = proj.get_clones_traffic()
                    # display base stats in the ui
                    repo_data_json["clones"]["count"] = clones["count"]
                    repo_data_json["clones"]["uniques"] = clones["uniques"]
                    # save more specific stats for charts later
                    #print(clones)
                    if url not in stats_data:
                        stats_data[url] = {}
                    for clone in clones["clones"]:
                        cur_time = clone.timestamp.strftime("%Y-%m-%d")
                        if cur_time in stats_data[url]:
                            stats_data[url][cur_time] = {
                                **stats_data[url][cur_time],
                                "clones": {
                                    "unique": clone.uniques,
                                    "count": clone.count
                                }
                            }
                        else:
                            stats_data[url][cur_time] = {
                                "clones": {
                                    "unique": clone.uniques,
                                    "count": clone.count
                                },
                                "traffic": {
                                    "count": 0,
                                    "unique": 0
                                },
                                "referrer": {}
                            }
                    traffic = proj.get_views_traffic()
                    #print(traffic)
                    for t in traffic['views']:
                        cur_time = t.timestamp.strftime("%Y-%m-%d")
                        if cur_time in stats_data[url]:
                            stats_data[url][cur_time] = {
                                **stats_data[url][cur_time],
                                "traffic": {
                                    "count": t.count,
                                    "unique": t.uniques
                                }
                            }
                        else:
                            stats_data[url][cur_time] = {
                                "traffic": {
                                    "count": t.count,
                                    "unique": t.uniques
                                },
                                "clones": {
                                    "unique": 0,
                                    "count": 0
                                },
                                "referrer": {}
                            }
                    traffic_view_sources = requests.get(f"{url}/traffic/popular/referrers", headers=headers)
                    if traffic_view_sources.status_code == 200:
                        traffic_sources = json.loads(traffic_view_sources.text)
                        #print(traffic_sources)
                        today = datetime.today().strftime("%Y-%m-%d")
                        referrers = {}
                        for ref in traffic_sources:
                            referrers[ref["referrer"]] = {
                                "count": ref["count"],
                                "unique": ref["uniques"]
                            }
                        if today in stats_data[url]:
                            stats_data[url][today] = {
                                **stats_data[url][today],
                                "referrer": referrers
                            }
                        else:
                            stats_data[url][today] = {
                                "referrer": referrers,
                                "clones": {
                                    "unique": 0,
                                    "count": 0,
                                },
                                "traffic": {
                                    "count": 0,
                                    "unique": 0,
                                }
                            }
                    else:
                        print(f"Failed to get traffic sources\n")
                except Exception as e:
                    print(f"Failed to get traffic for {url} - {e}")
                repo_data_json["latest"]["commit_date"] = time.mktime(
                    repo_data_json["latest"]["commit_date"].timetuple())

                # Add JSON to array
                jsonbase["data"].append(repo_data_json)
            else:
                print("ERROR: Cannot access " + url)

with open(mythicmeta_repos) as f:
    headers = {"authorization": "Bearer " + MYTHIC_META_GITHUB_TOKEN,
               "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    g = Github(MYTHIC_META_GITHUB_TOKEN)
    for repository in f.readlines():
        if repository == "":
            continue  # skip blanks
        else:
            # Get Category and Project from line
            value = repository.split(",")
            category = value[0].strip()
            project = value[1].strip()
            url = api_url_base + project
            # Get GitHub Repo JSON from API
            print(url)
            proj = g.get_repo(project)
            print(f"{proj.name} - {proj.description}")
            latest = {
                "branch": "main",
                "commit_message": "",
                "commit_date": datetime.strptime("1970-01-01 00:00:01", "%Y-%m-%d %H:%M:%S"),
                "icon": "",
            }
            for b in proj.get_branches():
                branch = proj.get_branch(b.name)
                if branch.commit.commit.author.date > latest["commit_date"]:
                    latest = {
                        "branch": b.name,
                        "commit_message": branch.commit.commit.message,
                        "commit_date": branch.commit.commit.author.date,
                    }
            result = requests.get(url, headers=headers)
            if result.status_code == 200:
                repo_data_json = json.loads(result.text)
                if len(latest["branch"]) > 20:
                    latest["branch"] = latest["branch"][:20] + "..."
                if len(latest["commit_message"]) > 60:
                    latest["commit_message"] = latest["commit_message"][:60] + "..."
                repo_data_json["latest"] = latest
                # Add custom category field to JSON
                repo_data_json['category'] = category
                repo_data_json["clones"] = {
                    "count": -1,
                    "uniques": -1
                }
                try:
                    clones = proj.get_clones_traffic()
                    repo_data_json["clones"]["count"] = clones["count"]
                    repo_data_json["clones"]["uniques"] = clones["uniques"]
                    print(clones)
                    if url not in stats_data:
                        stats_data[url] = {}
                    for clone in clones["clones"]:
                        stats_data[url][clone.timestamp.strftime("%Y-%m-%d")] = {
                            "clones": {
                                "unique": clone.uniques,
                                "count": clone.count
                            },
                            "traffic": {
                                "count": 0,
                                "unique": 0
                            }
                        }
                    traffic = proj.get_views_traffic()
                    print(traffic)
                    for t in traffic['views']:
                        if t.timestamp.strftime("%Y-%m-%d") in stats_data[url]:
                            stats_data[url][t.timestamp.strftime("%Y-%m-%d")] = {
                                **stats_data[url][t.timestamp.strftime("%Y-%m-%d")],
                                "traffic": {
                                    "count": t.count,
                                    "unique": t.uniques
                                }
                            }
                        else:
                            stats_data[url][t.timestamp.strftime("%Y-%m-%d")] = {
                                "traffic": {
                                    "count": t.count,
                                    "unique": t.uniques
                                },
                                "clones": {
                                    "unique": 0,
                                    "count": 0
                                }
                            }
                except Exception as e:
                    print(f"Failed to get traffic for {url} - {e}")
                repo_data_json["latest"]["commit_date"] = time.mktime(
                    repo_data_json["latest"]["commit_date"].timetuple())

                # Add JSON to array
                jsonbase["data"].append(repo_data_json)
            else:
                print("ERROR: Cannot access " + url)


with open(datajson, 'w') as f:
    f.write(json.dumps(jsonbase, indent=2))
with open(stats_file, 'w') as f:
    f.write(json.dumps(stats_data, indent=2))
