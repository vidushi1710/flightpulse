package com.flightpulse.backend.controller;

import java.util.Map;

import com.flightpulse.backend.service.PythonMlService;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api/flights")
public class FlightController {

    private final PythonMlService pythonMlService;

    public FlightController(PythonMlService pythonMlService) {
        this.pythonMlService = pythonMlService;
    }

    @GetMapping("/live")
    public Map<String, Object> getLiveFlights(
            @RequestParam(defaultValue = "JFK") String airport,
            @RequestParam(defaultValue = "10") int limit) {

        if (!airport.matches("(?i)[a-z]{3}")) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "Airport must be a three-letter IATA code."
            );
        }

        if (limit < 1 || limit > 100) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST,
                    "Limit must be between 1 and 100."
            );
        }

        return pythonMlService.getLiveFlights(airport.toUpperCase(), limit);
    }

    @PostMapping("/predict")
    public Map<String, Object> predictFlight(
            @RequestBody Map<String, Object> flightData) {

        return pythonMlService.predictFlight(flightData);
    }
}
