from vercel_wsgi import VercelWSGI

from app import app

vercel_app = VercelWSGI(app)
