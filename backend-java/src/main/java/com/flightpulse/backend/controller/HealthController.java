package com.flightpulse.backend.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class HealthController {

    @GetMapping("/")
    public Map<String, String> home() {
        return Map.of(
            "application", "FlightPulse",
            "status", "running",
            "message", "FlightPulse backend is operational"
        );
    }

    @GetMapping("/api/health")
    public Map<String, String> health() {
        return Map.of(
            "status", "healthy",
            "service", "Spring Boot"
        );
    }
}
