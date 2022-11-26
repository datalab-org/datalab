# Design document: user authentication and authorization

Consider the following user stories:

1. A new group member wishes to use datalab.
    - They visit the deployment for the group and click "Login -> Login with ORCID".
    - This triggers the ORCID OAuth2 flow, first redirecting them to the ORCID login page to enter their details (and potentially perform 2FA) for ORCID, which will then redirect them back to a datalab API URL (not app) and yield an OAuth2 token to the server.
    - The server then has limited access to the user's ORCID data, e.g., names, affiliations.
    - The server can then decide whether to store the OAuth2 token to allow it to keep the user's ORCID data up to date; I think it makes more sense to register a datalab user using the ORCID info as it was first found, and then provide a datalab-specific edit page for the user's info.
    - This will then trigger a lookup in the the `users` collection to see if there are any `Person` objects with identities containing the same ORCID, if not, a new entry will be created that stores their ORCID identity alongside some metadata attached to the user.
    - If there was already a `Person` object with that ORCID identity, the person object should be updated with the data from ORCID, and the identity should be set to `verified = True`, which will give the new user read access to any data objects that are attached to their ORCID.
    - This process also leaves a session cookie in the user's browser which is associated with the verified ORCID login.
    - Now, this user can be attached to other data entries via free text search on their name, ORCID ID or any attached email.

2. An existing user has been attached to a data entry by name or by email that is not associated with their account.
    - In this scenario, there should be a page for each unattached/unverified "person" object that can be used to "claim" that person.
    - If the person object only contains a name and no identities, this process should send an email to an admin for them to confirm the merge, which will delete the unverified and unlink the old person object and replace it with the user's ID.
    - If the person object contains unverified identities, like an ORCID or an email address, then the appropriate verification flow should be followed, e.g., if the user has an attached ORCID, the person objects should be merged if they ORCIDs match, similarly for a verified email or institutional account.
