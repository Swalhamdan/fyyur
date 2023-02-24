#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
from datetime import datetime
import sys
from Models import db, Artist, Venue, Shows
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#
current_time = datetime.today()

@app.route('/')
def index():
  return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.order_by(Venue.id, Venue.state, Venue.city).all()
  data = []
  venue_state_city_exist = ''

  for venue in venues:
    upcoming_shows = list(filter(lambda x: x.start_time > current_time, venue.shows))

    if venue_state_city_exist == venue.city + venue.state:
      info = {
        'id': venue.id, 
        'name': venue.name, 
        'num_upcoming_shows': len(upcoming_shows)
      }
        
      data[len(data)-1] ['venues'].append(info)

    else:
      venue_state_city_exist = venue.city + venue.state
      info = {
        'city': venue.city,
        'state': venue.state,
        'venues': [{
          'id': venue.id,
          'name': venue.name,
          'num_upcoming_shows': len(upcoming_shows)
        }]
      }
      data.append(info) 


  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_input = request.form['search_term']
  venue = Venue.query.filter(Venue.name.ilike('%' + search_input +'%'))

  venues = list(map(Venue.venue_details, venue))
  response = {
    'count': len(venues),
    'data': venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
    
  upcoming_shows_query = list(filter(lambda x: x.start_time >= current_time, venue.shows))
  past_shows_query = list(filter(lambda x: x.start_time < current_time, venue.shows))

  past_shows = list(map(lambda x: x.show_artist(), upcoming_shows_query))
  upcoming_shows = list(map(lambda x: x.show_artist(), past_shows_query))

  data = {
    'id': venue.id,
    'name': venue.name,
    'city': venue.city,
    'state': venue.state,
    'address': venue.address,
    'phone': venue.phone,
    'genres': venue.genres.split(','),  
    'image_link': venue.image_link,
    'facebook_link': venue.facebook_link,
    'website': venue.website,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description
  }

  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_venue.html', venue=data)

#  ----------------------------------------------------------------
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  error = False 

  try:
    venue = Venue()
    seeking_talent = False
    seeking_description = ''
    if 'seeking_talent' in request.form:
      seeking_talent = request.form['seeking_talent'] == 'y'
      venue.seeking_talent = True
    if 'seeking_description' in request.form:
      seeking_description = request.form['seeking_description']

    
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    temp_genres = request.form.getlist('genres')
    venue.genres = ','.join(temp_genres)
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.image_link = request.form['image_link']
    venue.seeking_description = request.form['seeking_description']

    db.session.add(venue)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()
    
    if error:
      flash('An error occured. Venue ' + request.form['name'] + ' Could not be listed.')
    
    else:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except():
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if error:
    error(500)

  return None

#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_input = request.form['search_term']
  artist = Artist.query.filter(Artist.name.ilike('%' + search_input +'%'))

  artists = list(map(Artist.artist_details, artist))

  response = {
    'count': len(artists),
    'data': artists
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)

  past_shows_q = list(filter(lambda x: x.start_time < datetime.today(), artist.shows))  
  upcoming_shows_q = list(filter(lambda x: x.start_time >=  datetime.today(), artist.shows))

  past_shows = list(map(lambda x: x.show_venue(), past_shows_q))
  upcoming_shows = list(map(lambda x: x.show_venue(), upcoming_shows_q))  

  data = {
    'id': artist.id,
    'name': artist.name,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'genres': artist.genres.split(','),  
    'image_link': artist.image_link,
    'facebook_link': artist.facebook_link,
    'website': artist.website,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description
  }

  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_artist.html', artist=data)

#  ----------------------------------------------------------------
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False

  try:
    artist = Artist()
    seeking_venue = False
    seeking_description = ''
    if 'seeking_venue' in request.form:
      seeking_venue = request.form['seeking_venue'] == 'y'
      artist.seeking_venue = True
    if 'seeking_description' in request.form:
      seeking_description = request.form['seeking_description']

    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    temp_genres = request.form.getlist('genres')
    artist.genres = ','.join(temp_genres)
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    artist.image_link = request.form['image_link']
    artist.seeking_description = request.form['seeking_description']


    db.session.add(artist)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  
  finally:
    db.session.close()
    
    if error:
      return redirect(url_for('server_error'))
    
    else:
      return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Artist.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False

  try:
    venue = Venue()
    seeking_talent = False
    seeking_description = ''
    if 'seeking_talent' in request.form:
      seeking_talent = request.form['seeking_talent'] == 'y'
      venue.seeking_talent = True
    if 'seeking_description' in request.form:
      seeking_description = request.form['seeking_description']

    
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    temp_genres = request.form.getlist('genres')
    venue.genres = ','.join(temp_genres)
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.image_link = request.form['image_link']
    venue.seeking_description = request.form['seeking_description']

    db.session.add(venue)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  
  finally:
    db.session.close()
    
    if error:
      return redirect(url_for('server_error'))
    
    else:
      return redirect(url_for('show_venue', venue_id=venue_id))
  return redirect(url_for('show_venue', venue_id=venue_id))

#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False

  try:
    artist = Artist()
    seeking_venue = False
    seeking_description = ''
    if 'seeking_venue' in request.form:
      seeking_venue = request.form['seeking_venue'] == 'y'
      artist.seeking_venue = True
    if 'seeking_description' in request.form:
      seeking_description = request.form['seeking_description']

    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    temp_genres = request.form.getlist('genres')
    artist.genres = ','.join(temp_genres)
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    artist.image_link = request.form['image_link']
    artist.seeking_description = request.form['seeking_description']

    db.session.add(artist)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()
    
    if error:
      flash('An error occured. Artist ' + request.form['name'] + ' Could not be listed.')
    
    else:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Shows.query.all()
  data = []
  for show in shows:
    info = {
      'venue_id': show.venue.id, 
      'venue_name': show.venue.name,
      'artist_id': show.artist.id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.isoformat()
    }
    data.append(info)

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  error = False

  try:
    show = Shows()
    show.artist_id = request.form['artist_id']
    show.venue_id = request.form['venue_id']
    show.start_time = request.form['start_time']
    db.session.add(show)
    db.session.commit()

  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())

  finally:
    db.session.close()
    
    if error:
       flash('An error occurred. Requested show could not be listed.')
    
    else:
      flash('Show was successfully listed!')

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
