import viddlerv2
v = viddlerv2.ViddlerV2('00000000000031337', debug=True)
#print v.get('viddler.api.getInfo')
#print v.get('viddler.users.getProfile', {'user': 'todd'})
#print v.get('viddler.api.getInfo')
#print v.get('viddler.videos.getByUser', {'user': 'todd'})
print v.auth('todd', 'elitepassword')
print v.post('viddler.videos.delete', {'video_id': '2aa1b444'})
