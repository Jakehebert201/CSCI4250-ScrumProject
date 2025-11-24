## 9. Additional Helpful Information

### A. Known Issues and Limitations
- Location accuracy varies across devices.    
- Database must be manually reseeded after schema changes.  
- Some mobile browsers block background geolocation updates.

### B. Helpful Tips for Testing
- Use Chrome DevTools → **Sensors** panel to simulate GPS movement.  
- Use test accounts:
  - Professor: `professor@test.com / Test123!`
  - Student: `student@test.com / Test123!`
- For notifications, ensure push permissions are granted in the browser.

### C. Quick API Summary
| Endpoint | Method | Purpose |
|---------|--------|---------|
| `/app/update_location` | POST | Update student GPS location |
| `/app/clock_event` | POST | Clock in/out |
| `/app/classes/enroll/<id>` | POST | Enroll in class |
| `/app/api/notifications/send` | POST | Send or schedule notifications |

### D. How to Reset the Database
Run the following:
```
rm instance/studenttracker.db
python scripts/setup_database.py
```

