PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE Posts (ID TEXT, VIEWS INTEGER, OWNER INTEGER, BODY TEXT, TITLE TEXT);
/****** CORRUPTION ERROR *******/
CREATE TABLE Comments (PostID TEXT, CommentID TEXT, OWNER INTEGER, BODY TEXT);
INSERT INTO Comments VALUES('166caf34-bdc7-4cf9-aa8c-ac5ec43834d5','dd422053-7fa5-4584-a6f1-5b4f874cdc63',1.0058904355238970981e+20,'hayir basmindfd');
INSERT INTO Comments VALUES('166caf34-bdc7-4cf9-aa8c-ac5ec43834d5','97a8fe71-9e86-49fe-ae79-a0320b7da597',1.0058904355238970981e+20,'asdfgsasdfgsd');
INSERT INTO Comments VALUES('166caf34-bdc7-4cf9-aa8c-ac5ec43834d5','99741d36-a403-47ea-accf-82be1a7a3243',1.0058904355238970981e+20,'asdfghjhgfdsasdfghgfds');
INSERT INTO Comments VALUES('166caf34-bdc7-4cf9-aa8c-ac5ec43834d5','bd7a2397-e1e4-453d-8d3f-8f80b67d5e67',1.0058904355238970981e+20,'asdfhjhgfsasdfghjkjhgfdsadfgh');
INSERT INTO Comments VALUES('166caf34-bdc7-4cf9-aa8c-ac5ec43834d5','eb4933f7-f960-42d0-aa92-a8e58a11d072',1.0058904355238970981e+20,'here is a fun comment bro   ');
INSERT INTO Comments VALUES('166caf34-bdc7-4cf9-aa8c-ac5ec43834d5','19156a33-d047-488d-a4f0-381b76414f7d',1.0058904355238970981e+20,'noooo youuuuuuu smoopy');
INSERT INTO Comments VALUES('166caf34-bdc7-4cf9-aa8c-ac5ec43834d5','bad7ff5d-a9c3-46ce-a710-502464ce7ccb',1.0058904355238970981e+20,'Su su cok sogukdir');
INSERT INTO Comments VALUES('166caf34-bdc7-4cf9-aa8c-ac5ec43834d5','3528610f-3b2a-4ba6-b3a7-12a6cb003304',1.0058904355238970981e+20,'asdfghjhgfdsadfghj');
INSERT INTO Comments VALUES('166caf34-bdc7-4cf9-aa8c-ac5ec43834d5','e6f36e05-fa62-4302-bfb3-c10fbded23d3',1.0058904355238970981e+20,'ohh yeahh brooos');
INSERT INTO Comments VALUES('166caf34-bdc7-4cf9-aa8c-ac5ec43834d5','830fc6d7-3253-4f54-ac7f-ff59c45c701d',1.0058904355238970981e+20,'asdfghjkldfsfghjkljhgfd');
INSERT INTO Comments VALUES('166caf34-bdc7-4cf9-aa8c-ac5ec43834d5','252293ed-c197-48cb-9b24-3f48cfff4a05',1.0058904355238970981e+20,'Why are my comments failing lol?');
INSERT INTO Comments VALUES('8d449e4a-9c8d-4a61-85e1-85c937edee3a','4de0c937-2e08-4354-a691-04bf7e490be1',1.0058904355238970981e+20,'Nice here is a comment to take down!');
INSERT INTO Comments VALUES('5fb884cb-b7ac-4894-830a-f138a214584e','53186071-5f23-413b-8efc-bb3389d556bf',1.0058904355238970981e+20,'whjklijhgfdsa');
ROLLBACK; -- due to errors
