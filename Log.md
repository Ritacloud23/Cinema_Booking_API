ScreenHive Problems and Solutions
This file documents the major problems encountered while building the ScreenHive backend, the causes of those problems, how they were resolved, and the lessons learned.
1. Environment Variables Exposed to Git
Problem
The .env file was appearing in GitHub even though it contained local configuration and secrets.
Cause
The .env file had not been properly excluded from Git tracking.
Solution
Added .env to .gitignore and removed the already tracked file from Git using:

git rm --cached .env
Lesson
Secrets and environment-specific configuration should never be committed to the repository.

2. GitHub Actions Could Not Connect to PostgreSQL
Problem
The CI pipeline failed because the application could not connect to a database during testing.
Cause
GitHub Actions did not have the PostgreSQL database that the application expected.
Solution
Added PostgreSQL as a service inside the GitHub Actions workflow and supplied the required environment variables.
Lesson
CI needs its own predictable test environment. Local configuration should not be assumed to exist inside GitHub Actions.

3. Swagger Login Returned 422
Problem
The login endpoint returned a 422 Unprocessable Entity error when using Swagger's OAuth2 authorization.
Cause
Swagger's OAuth2 password flow sends credentials as form data, while our endpoint was initially expecting JSON.
Solution
Installed python-multipart and changed the login endpoint to use OAuth2PasswordRequestForm.
Lesson
The authentication flow used by the API documentation must match the data format expected by OAuth2.

4. Hold Endpoint Returned 500
Problem
Creating a seat hold caused a server error.
Cause
The hold service imported select from SQLAlchemy while using SQLModel.Session.exec().
This caused the query result to behave like a SQLAlchemy Row instead of returning the SeatInventory object directly.
The code eventually failed when accessing:

seat.status
Solution
Changed the import from:

from sqlalchemy import select
to:

from sqlmodel import Session, select
Result
The query returned the expected SeatInventory object and the hold operation worked correctly.
The seat successfully changed from:

AVAILABLE → HELD
Lesson
When using SQLModel, use SQLModel's select with Session.exec() so the returned objects behave as expected.

5. Booking Amount Was Initially Incorrect
Problem
The booking needed to have the correct ticket amount.
Cause
The booking implementation initially did not have a proper connection between the booking amount and the Showtime ticket price.
Solution
Added ticket_price to the Showtime model and made the booking service obtain the amount from the Showtime associated with the selected seat.
Lesson
The booking amount should come from trusted server-side data rather than being supplied by the client.

6. Booking Was Marking the Seat as Booked Too Early
Problem
We identified that changing the seat directly to booked when creating a booking would be incorrect because payment had not yet succeeded.
Cause
Booking creation and payment confirmation are separate stages in the workflow.
Solution
The booking now starts with:

Booking: pending
Seat: held
Payment confirmation will later transition the booking and seat to their confirmed states.
Lesson
Database state should represent the actual business process. A booking request is not the same thing as a successful payment.

7. Git Rebase Conflict
Problem
Git reported conflicts while synchronizing the branch with the remote repository.
Cause
Local and remote branches had different changes to the same files, including the GitHub Actions workflow.
Solution
The conflicting files were reviewed, the correct version was kept, the conflicts were marked as resolved, and the rebase was completed.
Lesson
Before merging or rebasing, understand what each side changed instead of blindly accepting one version.

8. Missing Screen Endpoints
Problem
The Screen model existed, but Screen endpoints were not appearing in Swagger.
Cause
The Screen router had not been created and registered with the FastAPI application.
Solution
Created the Screen schema, service, and router, then included the router in main.py.
Lesson
Creating a database model does not automatically expose API functionality. The model, service, router, and application registration all need to be connected.

9. Hold Concurrency and the Thundering Herd
Problem
Multiple users may attempt to hold the same cinema seat at almost the same time.
Risk
Without proper database locking, two requests could potentially read the seat as available before either request updates it.
Solution
The hold service uses a database transaction and row-level locking:

.with_for_update()
The first transaction locks the seat while it performs the availability check and creates the hold.
A competing transaction must wait until the first transaction finishes.
Expected Result

User A → locks seat → creates hold → commits
                                      ↓
User B → waits → checks seat → 409 Conflict
Lesson
The database, not application timing or luck, must protect the seat from concurrent booking attempts.

10. No Separate Test Database
Problem
Our test files existed, but there was no separate database for automated tests. Running tests against the development database could modify or destroy actual ScreenHive development data.
Cause
We initially had only one PostgreSQL database: screenhive.
Solution
Created a dedicated PostgreSQL database called screenhive_test inside the existing PostgreSQL container.
The test database was then populated with the same 10 tables used by ScreenHive:

users
films
screens
showtimes
seat_inventory
holds
bookings
booking_seats
payments
processed_events
Lesson
Automated tests should run against an isolated database so test operations cannot affect development data.