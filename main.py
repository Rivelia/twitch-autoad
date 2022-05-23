from streamlink import Streamlink
import cv2
import pytesseract
import time
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope
import config

pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH

def stream_to_url(url, quality='best'):
    session = Streamlink()
    streams = session.streams(url)
    if streams:
        return streams[quality].to_url()
    raise ValueError('Could not locate the stream.')

# Create instance of twitch API and create app authentication
twitch = Twitch(config.TWITCH_APP_ID, config.TWITCH_APP_SECRET)

# Open browser for twitch authentication
target_scope = [AuthScope.CHANNEL_EDIT_COMMERCIAL]
auth = UserAuthenticator(twitch, target_scope, force_verify=False)
# Open default browser and prompt with the twitch verification website
token, refresh_token = auth.authenticate()

# Add User authentication
twitch.set_user_authentication(token, target_scope, refresh_token)

# Get ID of user
user_info = twitch.get_users(logins=[config.TWITCH_USERNAME])
user_id = user_info['data'][0]['id']
print('Your user ID: ' + str(user_id))

url = 'https://www.twitch.tv/' + config.TWITCH_USERNAME
stream_url = stream_to_url(url, config.TWITCH_VIDEO_CAPTURE_QUALITY)

cap = cv2.VideoCapture(stream_url)
nextTimeToCheck = 0
while True:
    success, frame = cap.read()
    if not success:
        break

    if time.time() < nextTimeToCheck:
        continue

    img = frame[int(frame.shape[0]/1.2):, int(frame.shape[1]/3):int(frame.shape[1]/1.5)]
    img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)[1]
    img = cv2.threshold(img, 127, 255, cv2.THRESH_TOZERO)[1]
    text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
    if "Matchmaking".lower() in text.lower():
        print("Matchmaking in progress, starting 90s commercial and waiting 15m")
        twitch.start_commercial(user_id, 90)
        nextTimeToCheck = time.time() + 900
        continue

    print("No matchmaking in progress")
    nextTimeToCheck = time.time() + 5
    if config.DEBUG_SAVE_IMAGES:
        cv2.imwrite('debug_img.png', img)
        cv2.imwrite('debug_frame.png', frame)

cap.release()
