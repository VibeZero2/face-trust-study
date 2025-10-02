#!/usr/bin/env python3
"""
Automate running through the study as a participant.
Usage: python scripts/auto_participant.py --pid 400
"""
import argparse
import time
import re

try:
    import requests
except Exception:
    print('The requests library is required. Install with: pip install requests')
    raise


def run_participant(base_url: str, pid: str):
    s = requests.Session()
    print('GET /')
    r = s.get(base_url + '/')
    print('->', r.status_code, r.url)

    # Consent
    print('GET /consent')
    r = s.get(base_url + '/consent')
    print('->', r.status_code)
    print('POST /consent (agree)')
    r = s.post(base_url + '/consent', data={'choice': 'agree'}, allow_redirects=True)
    print('->', r.status_code, r.url)

    # Start with pid
    print(f'POST /start pid={pid}')
    r = s.post(base_url + '/start', data={'pid': pid, 'prolific_pid': ''}, allow_redirects=True)
    print('->', r.status_code, r.url)

    # Walk through tasks until survey
    step = 0
    while True:
        step += 1
        print(f'GET /task (step {step})')
        r = s.get(base_url + '/task')
        # If redirected to survey, break
        if r.status_code in (301, 302) and '/survey' in r.headers.get('Location', ''):
            print('-> redirected to survey')
            break
        if r.status_code != 200:
            print('Unexpected status for /task:', r.status_code)
            break

        html = r.text
        # determine version
        m = re.search(r"name=[\"']version[\"']\s+value=[\"']([^\"']+)[\"']", html)
        version = m.group(1) if m else None
        if not version:
            # fallback heuristics
            if 'name="trust_full"' in html or 'name=\'trust_full\'' in html:
                version = 'full'
            else:
                version = 'toggle'

        print('Detected version:', version)
        if version == 'toggle':
            data = {
                'version': 'toggle',
                'trust_left': '5',
                'emotion_left': '3',
                'trust_right': '5',
                'emotion_right': '3',
                'masc_toggle': 'male',
                'fem_toggle': 'female'
            }
        else:
            data = {
                'version': 'full',
                'trust_full': '5',
                'emotion_full': '3',
                'masc': 'male',
                'fem': 'female'
            }

        print('POST /task', {k: v for k, v in data.items() if k in ('version', 'trust_full', 'trust_left')})
        r = s.post(base_url + '/task', data=data, allow_redirects=True)
        print('->', r.status_code, r.url)
        # small delay to avoid hammering
        time.sleep(0.1)

        # If after POST we landed on survey, break
        if '/survey' in r.url:
            print('Reached survey')
            break

    # Submit survey
    print('GET /survey')
    r = s.get(base_url + '/survey')
    print('->', r.status_code)
    survey_data = {
        'trust1': '5', 'trust2': '4', 'trust3': '5', 'trust4': '4', 'trust5': '5', 'trust6': '4',
        'tipi1': '3', 'tipi2': '3', 'tipi3': '4', 'tipi4': '2', 'tipi5': '4',
        'tipi6': '2', 'tipi7': '5', 'tipi8': '3', 'tipi9': '4', 'tipi10': '3'
    }
    print('POST /survey', survey_data)
    r = s.post(base_url + '/survey', data=survey_data, allow_redirects=True)
    print('->', r.status_code, r.url)

    # Done page
    r = s.get(base_url + '/done')
    print('GET /done ->', r.status_code)
    print('--- Done page start ---')
    print(r.text[:1000])
    print('--- Done page end ---')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pid', default='400')
    p.add_argument('--host', default='http://localhost:3000')
    args = p.parse_args()

    run_participant(args.host.rstrip('/'), args.pid)


if __name__ == '__main__':
    main()


