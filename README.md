# Ravyn
Ravyn is a fresh social media platform dedicated to being friendly.
## AI
An AI sentiment analysis model is being built to analyze posts, to keep the platform friendly. This is in a very very early phase, and is maxing out at 40% accuracy, well below the range where I would even consider integrating this into the site.
## Reports
The reports system lets anyone report posts for moderators to take down if they feel it violates the spirit of the platform.

## TODO/Contributions
We desperately need a TOS/Privacy Policy. I haven't gotten around to it, and I think if we are to grow any further, the moderators need an objective standard to hold people to.

At some point, I need to address the need to upgrade our current content system. People need to be able to post rich text, because some posts right now are very unaesthetic, I also think people will be more engaged if photos and videos can be posted.
I am putting this off for now because I need to make sure no malicious files can be uploaded to the server, and that the files aren't too large, and that the content is legal/ethical, etc. There is a whole host of issues to address here, and I currently don't feel like I am ready to tackle those. 

To run in a development environment, make sure to set the RAVYN_DEVELOPMENT_MODE environment variable to True, or the script won't call _app.run()_.
## State of the Project
The codebase has made a ton of progress, but above I only pointed out my wishlist and failures 😂  
Here are some features:
- Reports
- Comments
- Search
- Posts
- Profile Pictures
- Sorting posts by time posted
- Caching DB connections in the context of a single request
