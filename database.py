def get_enrollement_data_from_db():
    # db_url = "localhost:27017"
    db_url = "mongodb://admin:%40uditP%4055w0rd@34.221.247.48/admin"
    mongo_client = MongoClient(db_url)
    db = mongo_client["lifetechacademy"]
    return list(db["enrollmentForm"].find({}))