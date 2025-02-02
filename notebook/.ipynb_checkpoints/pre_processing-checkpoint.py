from pre_processing_funk import *
from analysis_funk import *

# File Urls
data_raw_path = '../data/raw'
notebook_path = '../../notebook'
url_paris_listings_data = 'http://data.insideairbnb.com/france/ile-de-france/paris/2018-08-13/data/listings.csv.gz'
url_paris_reviews_data = 'http://data.insideairbnb.com/france/ile-de-france/paris/2018-08-13/data/reviews.csv.gz'
name_of_main_folder = 'Project-Data-Mining'

project_path = '/Users/iZbra1/Documents/Jupyter-DS/K2DS/Projects/Project-Data-Mining/notebook'

# Download the listings
confirm_files(name_of_main_folder, url_paris_listings_data)
# Download the reviews
confirm_files(name_of_main_folder, url_paris_reviews_data)

# Change directory if necessary.
os.chdir(notebook_path)

print('Pre-Processing...')

# Load Raw Data
int_data = '../data/raw/listings.csv'
listings_columns_with_dates = ['last_scraped','host_since','first_review','last_review']
usecols = ['id','last_scraped']+columns_phase_1['summry']+columns_phase_1['host_info']+columns_phase_1['location']+columns_phase_1['prdct']+columns_phase_1['guest_info']+columns_phase_1['rvws']
listings = pd.read_csv(int_data, index_col=0, parse_dates=listings_columns_with_dates, usecols=usecols) #

# SUMMARY
# Listings that have a  null name?
lwn_name = listings.loc[listings.name.isnull()].index.values
# Listings that have a  null summary?
lwn_summary = listings.loc[listings.summary.isnull()].index.values
# Listings that have a  null description?
lwn_desc = listings.loc[listings.description.isnull()].index.values

# HOST_INFO
# Listings where host_since is  null       (28)
lwn_host_since = listings.loc[listings.host_since.isnull()].index.values
# Listings where host_is_superhost is  null ()
lwn_host_is_superhost = listings.loc[listings.host_is_superhost.isnull()].index.values

# LOCATION :
# Uniform to zipcode standard format (5 digits)
listings['zipcode'] = listings.zipcode.apply(clean_zip)
outlier_zipcodes = listings.loc[(listings.zipcode<=75000)|(listings.zipcode>76000),'zipcode'].unique()

# Merge 75106, 75116 to 75006 and 75016 respectively
listings.loc[listings.zipcode==75106, 'zipcode'] = 75006
listings.loc[listings.zipcode==75116, 'zipcode'] = 75016

# Add to the black list those zipcodes that are null or have a value of 1
lwn_num_zip = listings.loc[(listings.zipcode==0)|(listings.zipcode==1)|(listings.zipcode.isin(outlier_zipcodes))].index.values

# Listings where location is not exact
lwn_loc_exact = listings.loc[listings.is_location_exact=='f'].index.values

# PRODUCT
# Listings where bedroom or bathroom are null
lwn_beds_baths = listings.loc[(listings.bathrooms.isnull())|(listings.beds.isnull())].index.values

# REVIEWS
# Listings with null reviews
lwn_rvws = listings.loc[(listings.review_scores_accuracy.isnull())|
                        (listings.review_scores_checkin.isnull())|
                        (listings.review_scores_cleanliness.isnull())|
                        (listings.review_scores_communication.isnull())|
                        (listings.review_scores_rating.isnull())|
                        (listings.review_scores_location.isnull())|
                        (listings.review_scores_value.isnull())
                       ].index.values

# Build the Blacklist:
blacklist = list(set(np.concatenate((lwn_name,lwn_summary, lwn_desc,
                                lwn_host_since,lwn_host_is_superhost,
                                lwn_num_zip,lwn_loc_exact,lwn_beds_baths, lwn_rvws), axis=0)))

# Null-Free Updated Dataframe
null_free_row_data_index = listings.loc[~listings.index.isin(blacklist)].index.values

# Remove the % symbol from host_response_rate and convert to float
listings.loc[listings.host_response_rate.notnull(),'host_response_rate'] = listings.loc[listings.host_response_rate.notnull(),'host_response_rate'].replace('[\%,]', '', regex=True).astype(float)

# Construct the dataset summarized
sumry_col = []
for section in columns_phase_2:
    sumry_col+=columns_phase_2[section]
data = listings.loc[null_free_row_data_index, sumry_col]

# Convert host_listings_count from float to int
data.host_listings_count = data.host_listings_count.astype(int)
data.beds = data.beds.astype(int)

# Convert host_is_superhost, instant_bookable, require_guest_profile_picture, require_guest_phone_verification to bool
ctb = {'f': False, 't': True, 'nan':np.nan}
data.host_is_superhost = data.host_is_superhost.map(ctb)
data.instant_bookable = data.instant_bookable.map(ctb)
data.require_guest_profile_picture = data.require_guest_profile_picture.map(ctb)
data.require_guest_phone_verification = data.require_guest_phone_verification.map(ctb)

# Convert the response_rate, price values (price, extra_people, weekly and monthly price) into float
data.loc[:,'host_response_rate'] = data.host_response_rate.astype(float)
data.loc[:,'price'] = data.price.replace('[\$,]', '', regex=True).astype(float)
data.loc[:,'extra_people'] = data.extra_people.replace('[\$,]', '', regex=True).astype(float)
data.loc[:,'weekly_price'] = data.weekly_price.replace('[\$,]', '', regex=True).astype(float)
data.loc[:,'monthly_price'] = data.monthly_price.replace('[\$,]', '', regex=True).astype(float)

# Correct the host_listings_count value with the total listings the host has in paris only
hl_count = data.loc[:,['host_id','host_listings_count']].groupby('host_id').count().sort_values('host_listings_count', ascending=False)
data = pd.merge(data.reset_index().set_index('host_id'), hl_count, right_index=True, left_index=True)
data.reset_index(inplace=True)
data.set_index('id', inplace=True)
# Drop host_listings_count_x
data.drop('host_listings_count_x', axis=1, inplace=True)
# Rename the column host_listings_count_y to host_listings_count
data.rename(columns={'host_listings_count_y': 'host_listings_count'}, inplace=True)


# Get the common city value for each of the zipcodes in Paris
zip_data = data.loc[:,['city','zipcode','latitude','longitude']].set_index('zipcode')
zip_paris = pd.Series(data.zipcode.unique()[(data.zipcode.unique()>=75000)&(data.zipcode.unique()<76000)]).reset_index()
zip_paris.rename(columns={0:'zipcode'}, inplace=True)
zip_paris['city'] = zip_paris.zipcode.apply(lambda x: get_com_den_city(x, zip_data))

zip_paris.drop('index', axis=1, inplace=True)
# Manually fix the outlier (zipcode=75106)
zip_paris.loc[zip_paris.zipcode==75106, 'city'] = 'paris-16e-arrondissement'

zip_paris.set_index('zipcode', inplace=True)
zip_paris.head()

# Apply research on THE data dataframe
# Prep dataframe to be merged
data.drop('city',axis=1, inplace=True)
data.reset_index(inplace=True)
data.set_index('zipcode', inplace=True)
# Merge
data = pd.merge(data, zip_paris, right_index=True, left_index=True)
# Prep dataframe post-merge
data.reset_index(inplace=True)
data.set_index('id', inplace=True)
data.rename(columns={'city_y':'district', 'id':'listing_id'}, inplace=True)


# Correct incorrect zipcoded listings by assigning the geographically nearest zipcode center.

centroids, outliers = get_centroids_and_outliers(data)

# Function that returns the zipcode having the minimum euclidean
# distance with a particular listing x. Uses local variable centroids

def get_distEuclid_centroids(x):
    d = np.sqrt((centroids.longitude - x.longitude)**2 + (centroids.latitude - x.latitude)**2)
    return d.idxmin()


# For every outlier perform k nearest centroids (k=1).
# In the centroids set, we compute the distance to every outlier listing and the
# function get_distEuclid will return with the zipcode whose centroid is the nearest.

outliers['zipcode'] = outliers.apply(lambda x: get_distEuclid_centroids(x), axis=1).astype(int)
# Update the color of the listing to its corresponding zipcode
outliers['color'] = outliers.zipcode.apply(lambda x: cpzl[x])

# Add corrected outliers into database

data = pd.merge(data, outliers.loc[:,['zipcode']], right_index=True, left_index=True, how='outer')
# Get the index of those listings whose zipcode_y is not null.
new_zip = data.loc[data.zipcode_y.notnull()].index.values
data.loc[new_zip,'zipcode_x'] = data.loc[new_zip,'zipcode_y']
data['zipcode'] = data.zipcode_x.astype(int)
data.drop(['zipcode_x','zipcode_y'], axis=1, inplace=True)



# Get the tourist attractions coordinates
paris_attractions = get_paris_attractions_coordinates()

## SAVE
data.to_csv('../data/interim/data.csv')
paris_attractions.to_csv('../data/interim/paris_attractions.csv')
print('Pre-processing completed! File created: ../data/interim/data.csv\nNew dataset size:',data.shape)
