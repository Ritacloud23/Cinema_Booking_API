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

Problem: Tests passed locally but failed in GitHub Actions because screenhive_test did not exist in the fresh CI PostgreSQL environment.
Cause: The test database had been created manually in the local Docker PostgreSQL instance, but GitHub Actions creates a fresh PostgreSQL instance for every run.
Solution: Added a CI step that creates screenhive_test before running pytest.
Lesson: Local infrastructure changes do not exist in CI. Test environments must explicitly create all required resources.

11. Expired Hold Did Not Release the Seat

Problem
An expired hold could not be reclaimed by another user.

Cause
The hold service changed the expired Hold status to `expired`, but did not change the associated seat status from `held` back to `available`.

 Solution
Updated `create_hold()` so that when an active hold has expired, both states are updated:

python
existing_hold.status = "expired"
seat.status = "available"

Problem: Tests failed after adding Film.base_price
Problem
 After adding the required base_price field to the Film model, uv run pytest failed in tests/test_holds.py.
Cause
 Some test fixtures created Film objects without providing base_price. PostgreSQL therefore rejected the insert because base_price is a required NOT NULL column.
The error was:

sqlalchemy.exc.IntegrityError:
null value in column "base_price" of relation "films"
violates not-null constraint
Solution
 Updated the affected Film(...) objects in tests/test_holds.py to include:


base_price=5000,
We also cleaned up the repeated imports inside the test functions.
Lesson
 When a required database field is added to an existing model, all test fixtures and seed data that create that model must be updated. A model change isn't complete until the existing test data reflects the new schema.
And importantly, after the fix:

uv run pytest
passed successfully.

Firestore Environment Variable Configuration Error
Problem
The Firestore connection could not initialize because Pydantic Settings rejected FIREBASE_CREDENTIALS_PATH as an unknown configuration field.
Cause
The .env file contained an extra colon after the equals sign:

FIREBASE_CREDENTIALS_PATH:=firebase-service-account.json
The correct environment variable format is:

FIREBASE_CREDENTIALS_PATH=firebase-service-account.json
Although FIREBASE_CREDENTIALS_PATH was correctly defined in app/core/config.py, the malformed .env entry caused Pydantic Settings to interpret the configuration incorrectly and raise an extra_forbidden validation error.
Solution
Corrected the .env entry by removing the extra colon:

FIREBASE_CREDENTIALS_PATH=firebase-service-account.json
Lesson
Environment variables must follow the exact KEY=VALUE format. A small formatting error in .env can prevent the entire application configuration from loading, even when the corresponding setting is correctly defined in the Python configuration class.

## Firestore Live Board and SSE Integration

### Problem

ScreenHive needed to provide real-time showtime seat updates to clients. Changes to seat availability needed to be reflected in the live board without requiring clients to repeatedly refresh the API.

### Cause

PostgreSQL is the source of truth for seat state, while Firestore was introduced for stream-shaped live data. However, there was initially no connection between seat state changes in PostgreSQL and the Firestore live board or SSE stream.

This meant a seat could change from `available` to `held` in PostgreSQL without the live showtime board being updated.

### Solution

Implemented a Firestore live board for showtimes and an SSE endpoint for streaming updates to clients.

When a seat is successfully held:

1. PostgreSQL updates the seat state to `held`.
2. The transaction is committed.
3. Redis seat-map cache is invalidated.
4. The updated showtime board is published to Firestore.
5. The SSE endpoint detects the Firestore change.
6. The client receives a `showtime_update` event.

The integration was verified by creating a hold and observing the SSE stream change from:

`available_seats: 27, held_seats: 3`

to:

`available_seats: 26, held_seats: 4`.

### Lesson

Real-time data should have a clear source of truth and a deliberate data flow. PostgreSQL remains the authoritative source for seat state, while Firestore is used only for the live, stream-shaped representation. SSE then provides a persistent connection through which clients can receive those updates without repeatedly polling the API.