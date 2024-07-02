import collections
import collections.abc
import logging



"""
This module contains the MongoDB class, which is a wrapper around the
`motor.motor_asyncio.AsyncIOMotorClient` class. It provides a simple interface
to interact with a MongoDB database.
"""

class Document:
    def __init__(self,connection,document_name):
        """
        A class to represent a MongoDB document.
        This init function is used to create a new document object.
        :connection (Mongo Connection): The connection to the MongoDB database.
        :document_name (str): The name of the document.
        """
        self.db = connection[document_name]
        self.logger = logging.getLogger(__name__)

    async def find(self, query):
        """
        Find documents in the database that match the query.
        :param query (dict): The query to match documents.
        :return (list): A list of documents that match the query.
        """
        return await self.db.find(query).to_list(None)
    
    async def find_one(self, query):
        """
        Find a document in the database that matches the query.
        :param query (dict): The query to match a document.
        :return (dict): The document that matches the query.
        """
        return await self.db.find_one(query)

    async def insert_one(self, document):
        """
        Insert a document into the database.
        :param document (dict): The document to insert.
        """
        if not isinstance(document, collections.abc.Mapping):
            raise TypeError('document must be a mapping')
        
        await self.db.insert_one(document)

    async def update(self, query, update):
        """
        Update a document in the database.
        :param query (dict): The query to find the document.
        :param update (dict): The update to apply to the document.
        """
        if not isinstance(query, collections.abc.Mapping):
            raise TypeError('query must be a dictionary')
        if not await self.db.find_one(query):
            await self.db.insert_one(query)
        await self.db.update_one(query, {'$set': update})
    
    async def find_by_id(self, id):
        """
        Find a document by its ID.
        :param id (str): The ID of the document.
        :return (dict): The document.
        """
        return await self.db.find_one({'_id': id})
    
    async def delete_by_id(self, id):
        """
        Delete a document by its ID.
        :param id (str): The ID of the document.
        """
        await self.db.delete_one({'_id': id})

    async def insert(self, document):
        """
        Insert a document into the database.
        :param document (dict): The document to insert.
        """
        if not isinstance(document, collections.abc.Mapping):
            raise TypeError('document must be a mapping')
        
        if not document["_id"]:
            raise ValueError('document must have an _id field')
        
        await self.db.insert_one(document)


    async def upsert(self, document):
        """
        Update a document in the database.
        :param document (dict): The document to update.
        If the document does not exist, it will be inserted.
        If the document exists, it will be updated.
        By default, the document will be updated with the new values.
        """
        if not isinstance(document, collections.abc.Mapping):
            raise TypeError('document must be a mapping')
        
        if not document["_id"]:
            raise ValueError('document must have an _id field')
        
        await self.db.update_one({'_id': document['_id']}, {'$set': document}, upsert=True)

    async def update_by_id(self, document):
        """
        Update a document by its _id. Insert if not exists.
        :param document (dict): The document to update.
        """
        if not isinstance(document, dict):
            raise TypeError('document must be a dictionary')

        if "_id" not in document:
            raise ValueError('document must have an _id field')

        existing_doc = await self.find_by_id(document["_id"])
        if existing_doc:
            await self.db.replace_one({"_id": document["_id"]}, document)
        else:
            await self.insert(document)

    async def unset(self,document):
        """
        To Delete a field in a document.
        Unset a field in a document.
        :param document (dict): The document to update.
        """
        if not isinstance(document, collections.abc.Mapping):
            raise TypeError('document must be a mapping')
        
        if not document["_id"]:
            raise ValueError('document must have an _id field')
        
        if not await self.find_by_id(document["_id"]):
            raise ValueError('document does not exist')
        
        id = document["_id"]
        document.pop("_id")
        await self.db.update({'_id': id}, {'$unset': document})

    async def increment(self,id,field,value):
        """
        Increment a field in a document.
        :param id (str): The ID of the document.
        :param field (str): The field to increment.
        :param value (int): The value to increment by.
        """

        if not await self.find_by_id(id):
            raise ValueError('document does not exist')
        
        await self.db.update_one({'_id': id}, {'$inc': {field: value}})

    async def get_all(self):
        """
        Get all documents in the collection.
        :return (list): A list of documents.
        """
        return await self.db.find({})
    
