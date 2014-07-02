all: run

compile: ExtractKeywordsAndSaveToDB.java
	javac -cp .:keyxml.jar ExtractKeywordsAndSaveToDB.java

run: compile
	java -cp .:keyxml.jar ExtractKeywordsAndSaveToDB
