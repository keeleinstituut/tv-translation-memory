import requests
from Config.Config import G_CONFIG
from flask import request, jsonify
from src.RestApi.Auth import access_token

keycloak_config = G_CONFIG.config['keycloak']


class KeycloakHelper():

    def __init__(self):
        pass

    def get_token(self, username, password):
        data = {
            'grant_type': keycloak_config['grant_type'],
            'client_id': keycloak_config['client_id'],
            'client_secret': keycloak_config['client_secret'],
            'username': username,
            'password': password
        }
        url = ''.join([
            keycloak_config['url'],
            'realms/',
            keycloak_config['realm'],
            '/protocol/openid-connect/token'
        ])
        return self.send_request(url, 'POST', data=data)

    def refresh_token(self, refresh_token):
        headers = {
            'Authorization': 'Bearer ' + access_token()
        }
        data = {
            'grant_type': 'refresh_token',
            'client_id': keycloak_config['client_id'],
            'client_secret': keycloak_config['client_secret'],
            'refresh_token': refresh_token
        }
        url = ''.join([
            keycloak_config['url'],
            'realms/',
            keycloak_config['realm'],
            '/protocol/openid-connect/token'
        ])
        return self.send_request(url, 'POST', data=data, headers=headers)

    def get_user_info(self, user_id=None, username=None):
        headers = {
            'Authorization': 'Bearer ' + access_token()
        }
        url = ''.join([
            keycloak_config['url'],
            'admin/realms/',
            keycloak_config['realm'],
            '/users',
        ])
        if user_id is not None:
            url = url + '/' + user_id
        if username is not None:
            url = url + '?username=' + username
        return self.send_request(url, 'GET', headers=headers)

    def add_user(self, user_info):
        headers = {
            'Authorization': 'Bearer ' + access_token(),
            'Content-Type': 'application/json'
        }
        url = ''.join([
            keycloak_config['url'],
            'admin/realms/',
            keycloak_config['realm'],
            '/users',
        ])
        return self.send_request(url, 'POST', json=user_info, headers=headers)

    def edit_user(self, user_id, user_info):
        headers = {
            'Authorization': 'Bearer ' + access_token(),
            'Content-Type': 'application/json'
        }
        url = ''.join([
            keycloak_config['url'],
            'admin/realms/',
            keycloak_config['realm'],
            '/users/' + user_id,
        ])
        return self.send_request(url, 'PUT', json=user_info, headers=headers)

    def delete_user(self, user_id):
        headers = {
            'Authorization': 'Bearer ' + access_token(),
            'Content-Type': 'application/json'
        }
        url = ''.join([
            keycloak_config['url'],
            'admin/realms/',
            keycloak_config['realm'],
            '/users/' + user_id,
        ])
        return self.send_request(url, 'DELETE', headers=headers)

    def send_request(self, url, method, json=None, data=None, headers=None):
        response = requests.request(method, url, data=data, json=json, headers=headers)
        if response.status_code > 300:
            return {
                "message": "Error getting token from Keycloak: {}".format(response.text)
            }
        if response.text == '':
            return {'status': 'success'}

        tokens_data = response.json()
        return tokens_data


keycloak = KeycloakHelper()
