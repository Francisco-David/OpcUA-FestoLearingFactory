from opcua import ua, Server

# Initialize the server
server = Server()

# Load the XML configuration file
server.import_xml("./opcuaxml.xml")

# Define the endpoint URL for the server
url = "opc.tcp://localhost:4840"
server.set_endpoint(url)

# Get the root node of the server's address space
root_node = server.get_root_node()

# Start the server
server.start()
print("OPC UA server started at", url)
