# Database

For this project, a **BigQuery** database was used to store all the chat session data due to its capacity of reflecting new objects almost instantaneously, as well as for its analytics capacity due to it uses a columnar storage instead of a row storage, making it suitable for further data analysis.

Even when this database is really good for inserting new data, one of the great disadvantages found during the development of this project was its incapacity to delete recent objects, this is because it uses a streaming buffer, allowing to get the most updated data almost in near time. Nevertheless, while the most recent data is in this buffer, it is impossible or really hard to delete those records, which can be stored there for up to 90 minutes.

Taking into account that, it was decided to build four different tables, which allows to quickly build and retrieve the most recent user request and agent's responses, as well as keep the data normalized to avoid store repeated data:

- **Users**

Contains all the data related to the user, its email, full name, and other related fields. It is important to mention that raw passwords are never stored, instead, its hashed passwords are stored.

- **ChatSessions**

Contains all the data related to the chat session, such as who is the owner of the session and when it was created.

- **Prompts**

Each row is a user interaction, containing the its prompt and agent response, as well as the date when it was made.

- **AgentSteps**

This table contains all the steps that the agent had to process to get a response to the user. One single user prompt could generate nay agent steps. Which then are used to generate the whole chat history.
