import jwt
from flask_principal import Identity


class Keycloak:
    def __init__(self, url, realm):
        self.url = url
        self.realm = realm
        self.jwk_client = jwt.PyJWKClient(uri="{}/realms/{}/protocol/openid-connect/certs".format(self.url, self.realm))

    def get_jwk(self, kid):
        return self.jwk_client.get_signing_key(kid)
    
    
class KeycloakIdentity(Identity):
    def __init__(self, access_token, auth_type=None):
        institution_user_id = access_token['sub']
        super().__init__(
            id=institution_user_id,
            auth_type=auth_type)

        self.access_token = access_token

    @property
    def is_physical_user(self):
        return 'tolkevarav' in self.access_token

    @property
    def _tolkevarav_claim(self):
        return self.access_token.get('tolkevarav', {})

    @property
    def realm_access_roles(self):
        return self.access_token['realm_access']['roles']

    @property
    def institution_id(self):
        return self._tolkevarav_claim.get('selectedInstitution', {}).get('id')

    @property
    def institution_user_id(self):
        return self._tolkevarav_claim.get('institutionUserId')

    @property
    def institution_user_forename(self):
        return self._tolkevarav_claim.get('forename')

    @property
    def institution_user_surname(self):
        return self._tolkevarav_claim.get('surname')

    @property
    def institution_user_pic(self):
        return self._tolkevarav_claim.get('personalIdentificationCode')

    @property
    def department_id(self):
        return self._tolkevarav_claim.get('department', {}).get('id')

    @property
    def department_name(self):
        return self._tolkevarav_claim.get('department', {}).get('name')

    @property
    def privileges(self):
        return self._tolkevarav_claim.get('privileges')

    # Backwards compatibility purposes
    @property
    def scopes(self):
        return None

    # Backwards compatibility purposes
    @property
    def role(self):
        # return 'admin'
        return None
