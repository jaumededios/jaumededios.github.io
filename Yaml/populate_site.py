#!/usr/bin/env python

import yaml
from datetime import datetime,timedelta




################

talk_base =\
'''---
{title}

{event}\n{event_url}\n{location}

{date}\n{date_end}\n{all_day}
\n
{tags}
\n\n

\n\n
featured: false\nslides: ""\nprojects: []\nmath: true

{publishDate}
authors: []
---
{abstract}
'''


with open("talks.yaml", 'r') as stream:
    try:
        talks = yaml.safe_load(stream)
        for talk_id,talk in talks.items():
            print(talk_id)
            talk_data = {}

            for prop in ('title','event', 'event_url','date','date_end'):
                try:
                    talk_data[prop] = '{}: "{}"'.format(prop,talk[prop])
                except KeyError:
                    talk_data[prop] = ''

            if 'time_zone' in talk:
                talk_data['location'] = 'location: "[{}] {}"'.format(talk['time_zone'],
                                                                talk['event'])
            else:
                talk_data['location'] = 'location: "{}"'.format(talk['event'])

            if 'date_end' in talk:
                talk_data['all_day'] = 'all_day: false'
            else:
                talk_data['all_day'] = 'all_day: true'

            talk_data['tags'] = 'tags: '+str(["Talk"]+talk['tags'])
            talk_data['publishDate'] = 'publishDate: "{}{}"'.format(
                                            int(talk['date'][:4])-1,
                                            talk['date'][4:]
                                        )
            talk_data['abstract'] = talk['abstract']


            with open('md_talk/%s.md'%talk_id,'w') as f:
                f.write(talk_base.format(**talk_data))

    except yaml.YAMLError as exc:
        print(exc)


travel_base ='''---
title: "{title}"
event: "{title}"
event_url: {url}
external_link : {url}      
location: "{location}"
date: "{date}"
date_end: "{date_end}"
all_day: true
publishDate: "2017-01-01T00:00:00Z"

tags: {tags}
authors: []\nlinks: []\nprojects: []\nmath: true
---
'''


with open("travel.yaml", 'r') as stream:
    try:
        travel = yaml.safe_load(stream)
        for trip_id,trip in travel.items():
            print(trip_id)
            trip['tags'] = str(['Travel']+trip['tags'])


            with open('md_travel/%s.md'%trip_id,'w') as f:
                f.write(travel_base.format(**trip))

    except yaml.YAMLError as exc:
        print(exc)