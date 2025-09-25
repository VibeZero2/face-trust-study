from app import app

with app.test_client() as client:
    resp = client.get('/?PROLIFIC_PID=PID123&STUDY_ID=SID&SESSION_ID=SESS')
    print('initial', resp.status_code, resp.location)
    if resp.status_code in (301,302,303,307,308) and resp.location:
        resp = client.get(resp.location)
        print('after redirect to consent', resp.status_code)
    resp = client.post('/consent', data={'choice': 'agree'}, follow_redirects=False)
    print('post consent', resp.status_code, resp.location)
    next_url = resp.location
    if next_url:
        resp = client.get(next_url)
        print('after consent redirect', resp.status_code, resp.location)
        if resp.status_code in (301,302,303,307,308) and resp.location:
            resp = client.get(resp.location)
            print('final step', resp.status_code)
