import pymongo


# DB이름 바꿨으면함 faceDB.json
def access_db():
    client = pymongo.MongoClient()
    # db = client['test_db']
    # col = db['test_col']
    db = client['face_id']
    col = db['id']
    error_col = db['error']

    return client, db, col, error_col
