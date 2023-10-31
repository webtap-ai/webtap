# Generate a readme summary of an Apify Actor

I want you to make a summart of an Apify Actor readme.

## Context

### This is description of an Apify Actor
{description}

### This is the original readme of an Apify Actor
{readme}

---

## Instructions

I want you to make a summart of an Apify Actor readme:
 - The summary should be a json object with 1 single element; key readme_summary
{{
    "readme_summary" : "# Readme summary"
}}
 - Return summary in markdown format
 - Make sure to return the most important information of the readme in order to correctly run the actor (discard any marketing or irrelevant information)
 - The summary should be a string with the most important information of the readme
 
Now execute the summary and return it in json format. Make sure that the json returned is parsable by JSON.parse().