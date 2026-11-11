package com.flightpulse.backend.service;

import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.server.ResponseStatusException;

@Service
public class PythonMlService {

    private final RestClient restClient;

    public PythonMlService(
            @Value("${ml.service.base-url:http://localhost:8000}") String baseUrl) {
        this.restClient = RestClient.builder()
                .baseUrl(baseUrl)
                .build();
    }

    public Map<String, Object> getLiveFlights(String airport, int limit) {
        try {
            return restClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/live-flights")
                            .queryParam("departure_airport", airport)
                            .queryParam("limit", limit)
                            .build())
                    .retrieve()
                    .body(new ParameterizedTypeReference<Map<String, Object>>() {});
        } catch (RestClientResponseException ex) {
            throw new ResponseStatusException(
                    ex.getStatusCode().is4xxClientError()
                            ? ex.getStatusCode()
                            : HttpStatus.BAD_GATEWAY,
                    "Python ML service returned an error."
            );
        } catch (Exception ex) {
            throw new ResponseStatusException(
                    HttpStatus.SERVICE_UNAVAILABLE,
                    "Python ML service is unavailable."
            );
        }
    }

    public Map<String, Object> predictFlight(Map<String, Object> flightData) {
        try {
            return restClient.post()
                    .uri("/predict")
                    .body(flightData)
                    .retrieve()
                    .body(new ParameterizedTypeReference<Map<String, Object>>() {});
        } catch (RestClientResponseException ex) {
            throw new ResponseStatusException(
                    ex.getStatusCode().is4xxClientError()
                            ? ex.getStatusCode()
                            : HttpStatus.BAD_GATEWAY,
                    "Python ML service returned an error."
            );
        } catch (Exception ex) {
            throw new ResponseStatusException(
                    HttpStatus.SERVICE_UNAVAILABLE,
                    "Python ML service is unavailable."
            );
        }
    }
}
