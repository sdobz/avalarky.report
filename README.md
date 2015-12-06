# ky.re

Kyre is a project spawned from the idea that the easier something it is the more likely it is to be used. If it is easy to publish more people will share what they learn with the world.

## Installation

Due to the early nature of this project it is not easy to use. All I can say is go for it, I'm happy to help. Open an issue or send me an email to request a tutorial or ask for help

Usage (to create a clone of avalarky.report)

* Clone the repository locally
* Copy `avalarky.report.kyre.secret.example` to `avalarky.report.secret.kyre`
* Create all accounts needed:
  * Evernote Developer token [goto page](https://www.evernote.com/api/DeveloperToken.action)
  * Google Maps API server key with geocode permissions [documentation](https://developers.google.com/maps/documentation/geocoding/get-api-key) or [signup flow](https://console.developers.google.com/flows/enableapi?apiid=geocoding_backend&keyType=SERVER_SIDE&reusekey=true)
  * Amazon AWS credentials for S3 [iam console](https://console.aws.amazon.com/iam/home?#users)
* Create python environment `./bootstrap.sh`
* Run program `./kyre.py`

# Overview

This program downloads all notes from any evernote notebooks matching a pattern and publishes them to s3 as a static blog.

# TODO

* Properly handle deleting content, cascading through caches
* Download notes+metadata from evernote simultaneously if applicable
* Allow easier setup

