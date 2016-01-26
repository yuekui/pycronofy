import datetime
from pycronofy import settings
from pycronofy.auth import Auth
from pycronofy.datetime_utils import get_iso8601_string
from pycronofy.pagination import Pages
from pycronofy.request_handler import RequestHandler

class CronofyClient(object):
    """Client for cronofy web service.
    Performs authentication, and wraps API: https://www.cronofy.com/developers/api/
    """

    def __init__(self, client_id=None, client_secret=None, access_token=None, refresh_token=None):
        """
        Example Usage:

        CronofyClient(access_token='')
        CronofyClient(client_id='', client_secret='')

        :param string client_id: OAuth Client ID.
        :param string client_secret: OAuth Client Secret.
        :param string access_token: Access Token for User's Account.
        :param string refresh_token: Existing Refresh Token for User's Account.
        :param bool debug: Instantiate in debug mode. (Optional, default False).
        """
        self.auth = Auth(client_id, client_secret, access_token, refresh_token)
        self.request_handler = RequestHandler(self.auth)

    def account(self):
        """Get identifying information for the active account.

        :return: Account data.
        :rtype: ``dict``
        """
        return self.request_handler.get(endpoint='account')['account']

    def close_notification_channel(self, channel_id):
        """Close a notification channel to stop push notifications from being sent.

        :param string channel_id: The id of the notification channel.
        :return: Response
        :rtype: ``response``
        """
        return self.request_handler.delete(endpoint='channels/%s' % channel_id)

    def create_notification_channel(self, callback_url, calendar_ids=()):
        """Create a new channel for receiving push notifications.

        :param string callback_url: The url that will receive push notifications.
        Must not be longer than 128 characters and should be HTTPS.
        :return: Response
        :rtype: ``response``
        """
        data = {'callback_url': callback_url}
        if calendar_ids:
            data['filters'] = {'calendar_ids':calendar_ids}
        return self.request_handler.post('channels', data=data)

    def delete_event(self, calendar_id, event_id):
        """Delete an event from the specified calendar.
        :param string calendar_id: ID of calendar to insert/update event into.
        :param string event_id: ID of event to delete.
        :return: Response from _delete
        :rtype: ``Response``
        """
        return self.request_handler.delete(endpoint='calendars/%s/events' % calendar_id, params={'event_id': event_id})

    def get_authorization_from_code(self, code, redirect_uri=''):
        """Updates the authorization tokens from the user provided code.

        :param string code: Authorization code to pass to Cronofy.
        :param string redirect_uri: Optionally override redirect uri obtained from user_auth_link.
        :return: Dictionary containing auth tokens and response status.
        :rtype: ``dict``
        """
        response = self.request_handler.post(
            url='%s/oauth/token' % settings.API_BASE_URL, 
            data={
                'grant_type': 'authorization_code',
                'client_id': self.auth.client_id,
                'client_secret': self.auth.client_secret,
                'code': code,
                'redirect_uri': redirect_uri if redirect_uri else self.auth.redirect_uri,
        })
        data = response.json()
        self.auth.update(
            authorization_datetime=datetime.datetime.now(),
            access_token=data['access_token'],
            refresh_token=data['refresh_token'],
            expires_in=data['expires_in'],
        )
        return {
            'access_token': self.auth.access_token, 
            'refresh_token': self.auth.refresh_token, 
            'response_status': response.status_code,
        }

    def list_calendars(self):
        """Return a list of calendars available for the active account.

        :return: List of calendars (dictionaries).
        :rtype: ``list``
        """
        return self.request_handler.get(endpoint='calendars')['calendars']

    def list_profiles(self):
        """Get list of active user's calendar profiles.

        :return: Calendar profiles.
        :rtype: ``list``
        """
        return self.request_handler.get(endpoint='profiles')['profiles']

    def list_notification_channels(self):
        """Return a list of notification channels available for the active account.

        :return: List of notification channels (dictionaries).
        :rtype: ``list``
        """
        return self.request_handler.get(endpoint='channels')['channels']

    def read_events(self, 
        calendar_ids=(), 
        from_date=None, 
        to_date=None, 
        last_modified=None,
        tzid=settings.DEFAULT_TIMEZONE_ID, 
        only_managed=False,
        include_managed=True, 
        include_deleted=False,
        include_moved=False,
        localized_times=False,
        automatic_pagination=True):
        """Read events for linked account (optionally for the specified calendars).

        :param tuple calendar_ids: Tuple or list of calendar ids to pass to cronofy. (Optional).
        :param datetime.date from_date: Start datetime (or ISO8601 string) for query. (Optional).
        :param datetime.date to_date: End datetime (or ISO8601 string) for query. (Optional).
        :param datetime.datetime last_modified: Return items modified on or after last_modified. Datetime or ISO8601 string. (Optional).
        :param string tzid: Timezone ID for query. (Optional, default settings.DEFAULT_TIMEZONE_ID). Should match tzinfo on datetime objects.
        :param bool only_managed: Only include events created through the API. (Optional, default False)
        :param bool include_managed: Include events created through the API. (Optional, default True)
        :param bool include_deleted: Include deleted events. (Optional, default False)
        :param bool include_moved: Include moved events. (Optional, default False)
        :param bool localized_times: Return time values for event start/end with localization information. This varies across providers. (Optional, default False).
        :param bool automatic_pagination: Autonatically fetch next page when iterating through results (Optional, default True)
        :return: Wrapped results (Containing first page of events).
        :rtype: ``Pages``
        """
        results = self.request_handler.get(endpoint='events', params={
            'tzid': tzid, 
            'calendar_ids':calendar_ids,
            'from': get_iso8601_string(from_date), 
            'to': get_iso8601_string(to_date),
            'last_modified': get_iso8601_string(last_modified),
            'only_managed': only_managed,
            'include_managed': include_managed,
            'include_deleted': include_deleted,
            'include_moved': include_moved,
            'localized_times': localized_times,
        })
        return Pages(self.request_handler, results, 'events', automatic_pagination)

    def read_free_busy(self, 
        calendar_ids=(), 
        from_date=None, 
        to_date=None, 
        last_modified=None,
        tzid=settings.DEFAULT_TIMEZONE_ID, 
        include_managed=True, 
        localized_times=False,
        automatic_pagination=True):
        """Read free/busy blocks for linked account (optionally for the specified calendars).

        :param tuple calendar_ids: Tuple or list of calendar ids to pass to cronofy. (Optional).
        :param datetime.date from_date: Start datetime (or ISO8601 string) for query. (Optional).
        :param datetime.date to_date: End datetime (or ISO8601 string) for query. (Optional).
        :param string tzid: Timezone ID for query. (Optional, default settings.DEFAULT_TIMEZONE_ID). Should match tzinfo on datetime objects.
        :param bool include_managed: Include pages created through the API. (Optional, default True)
        :param bool localized_times: Return time values for event start/end with localization information. This varies across providers. (Optional, default False).
        :param bool automatic_pagination: Autonatically fetch next page when iterating through results (Optional, default True)
        :return: Wrapped results (Containing first page of free/busy blocks).
        :rtype: ``Pages``
        """
        results = self.request_handler.get(endpoint='free_busy', params={
            'tzid': tzid, 
            'calendar_ids':calendar_ids,
            'from': get_iso8601_string(from_date), 
            'to': get_iso8601_string(to_date),
            'include_managed': include_managed,
            'localized_times': localized_times,
        })
        return Pages(self.request_handler, results, 'free_busy', automatic_pagination)

    def refresh_access_token(self):
        """Refreshes the authorization token.

        :return: Response.
        :rtype: ``response``
        """
        response = self.request_handler.post(
            url='%s/oauth/token' % settings.API_BASE_URL, 
            data={
                'grant_type': 'refresh_token',
                'client_id': self.auth.client_id,
                'client_secret': self.auth.client_secret,
                'refresh_token': self.auth.refresh_token,
            }
        )
        data = response.json()
        self.auth.update(
            authorization_datetime=datetime.datetime.now(),
            access_token=data['access_token'],
            expires_in=data['expires_in'],
        )
        return response

    def revoke_authorization(self):
        """Revokes Oauth authorization.

        :return: Response.
        :rtype: ``response``
        """
        response = self.request_handler.post(
            url='%s/oauth/token/revoke' % settings.API_BASE_URL,
            data={
                'client_id': self.auth.client_id,
                'client_secret': self.auth.client_secret,
                'token': self.auth.access_token,
            }
        )
        self.auth.update(
            authorization_datetime=None,
            access_token=None,
            refresh_token=None,
            expires_in=0,
        )
        return response

    def upsert_event(self, calendar_id, event):
        """Inserts or updates an event for the specified calendar.

        :param string calendar_id: ID of calendar to insert/update event into.
        :param dict event: Dictionary of event data to send to cronofy.
        :return: Response from _post
        :rtype: ``Response``
        """
        for key in settings.EVENTS_REQUIRED_FIELDS:
            if not key in event:
                raise Exception('%s not found in event.' % key)
        event['start'] = get_iso8601_string(event['start'])
        event['end'] = get_iso8601_string(event['end'])
        return self.request_handler.post(endpoint='calendars/%s/events' % calendar_id, data=event)

    def user_auth_link(self, redirect_uri, scope='', state=''):
        """Generates a URL to send the user for OAuth 2.0

        :param string redirect_uri: URL to redirect the user to after auth.
        :param string scope: The scope of the privileges you want the eventual access_token to grant.
        :param string state: A value that will be returned to you unaltered along with the user's authorization request decision.
        (The OAuth 2.0 RFC recommends using this to prevent cross-site request forgery.)
        :return: authorization link
        :rtype: ``string``
        """
        if not scope:
            scope = ' '.join(settings.DEFAULT_OAUTH_SCOPE)
        self.auth.update(redirect_uri=redirect_uri)
        data = self.request_handler.get(
            url='%s/oauth/authorize' % settings.APP_BASE_URL,
            params={
                'response_type': 'code',
                'client_id': self.auth.client_id,
                'redirect_uri': redirect_uri,
                'scope': scope,
                'state': state,
            },
            return_json=False
        )
        return data.url

