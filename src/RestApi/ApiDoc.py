from flask import Blueprint

apidoc = Blueprint('apidoc', __name__,
                   static_folder='../../doc_build',
                   static_url_path='/apidoc')
