# Incluir routers
app.include_router(auth.router)
app.include_router(cameras.router)
app.include_router(events.router)
app.include_router(detection_settings.router)
app.include_router(users.router)
app.include_router(devices.router)
app.include_router(ai_models.router)
app.include_router(persons.router) 