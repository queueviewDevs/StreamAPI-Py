import motor.motor_asyncio

uri = "mongodb+srv://ericmuzzo:dirtbIke1*@queueview.fghak.mongodb.net/?retryWrites=true&w=majority&appName=Queueview"

client = motor.motor_asyncio.AsyncIOMotorClient(uri)
database = client.get_database("clients")

devices_collection = database.get_collection("devices")
users_collection = database.get_collection("users")

async def create_indexes():
    await devices_collection.create_index("device_id", unique=True)
    await users_collection.create_index("username", unique=True, name="username_unique")
    await users_collection.create_index("email", unique=True, name="password_unique")
    await users_collection.create_index({
        "username": "text",
        "name": "text",
        "email": "text"
    }, name="user_text_index")