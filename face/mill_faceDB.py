import pymongo


# DB이름 바꿨으면함 faceDB.json
class mill_faceDB(object):
    def __new__(cls):
        if not hasattr(cls,'instance'):
            cls.instance = super(mill_faceDB, cls).__new__(cls)
        return cls.instance


    def access_db(self):
        client = pymongo.MongoClient()
        db = client['444']
        col = db['test_col']
        # db = client['face_id']
        # col = db['id']
        error_col = db['error']

        n = list(col.find({}))
        names = [i['name'] for i in n]
        id = [j['id'] for j in n]


        return client, db, col, error_col, names, id
