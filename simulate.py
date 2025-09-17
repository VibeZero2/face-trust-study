import requests

s = requests.Session()
base = 'http://localhost:3000'

r = s.get(base + '/consent')
print('GET /consent', r.status_code)

r = s.post(base + '/consent', data={'choice': 'agree'}, allow_redirects=False)
print('POST /consent', r.status_code, 'Location', r.headers.get('Location'))

if r.is_redirect:
    target = r.headers['Location']
    if target.startswith('http'):
        r = s.get(target)
    else:
        r = s.get(base + target)
else:
    r = s.get(base + '/')

print('after consent', r.status_code)
print(r.text[:200])
