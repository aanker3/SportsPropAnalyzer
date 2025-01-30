package main

import (
	"crypto/tls"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path/filepath"
)

func main() {
	// Get the directory where the script is located
	exePath, err := os.Executable()
	if err != nil {
		log.Fatalf("Failed to determine executable path: %v", err)
	}
	scriptDir := filepath.Dir(exePath)

	// Define the file path to ensure it's saved in the same folder as the script
	fileName := filepath.Join(scriptDir, "prizepicks_props.json")

	// Delete the existing file if it exists
	if _, err := os.Stat(fileName); err == nil {
		err := os.Remove(fileName)
		if err != nil {
			log.Fatalf("Failed to delete existing file: %v", err)
		}
	}

	// Set up HTTP transport with TLS
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: false},
	}
	client := &http.Client{Transport: tr}
	req, err := http.NewRequest("GET", "https://api.prizepicks.com/projections?league_id=7&per_page=250&single_stat=true", nil)
	if err != nil {
		log.Fatal(err)
	}

	// Set HTTP headers
	req.Header.Set("Host", "api.prizepicks.com")
	req.Header.Set("Sec-Ch-Ua", `"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"`)
	req.Header.Set("Accept", "application/json")
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Sec-Ch-Ua-Mobile", "?1")
	req.Header.Set("User-Agent", "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36")
	req.Header.Set("Sec-Ch-Ua-Platform", `"Android"`)
	req.Header.Set("Origin", "https://app.prizepicks.com")
	req.Header.Set("Sec-Fetch-Site", "same-site")
	req.Header.Set("Sec-Fetch-Mode", "cors")
	req.Header.Set("Sec-Fetch-Dest", "empty")
	req.Header.Set("Referer", "https://app.prizepicks.com/")
	// req.Header.Set("Accept-Encoding", "gzip, deflate")
	req.Header.Set("Accept-Language", "en-US,en;q=0.9")
	req.Header.Set("If-Modified-Since", "Thu, 12 Jan 2023 19:23:47 GMT")

	// Make HTTP request
	resp, err := client.Do(req)
	if err != nil {
		log.Fatal(err)
	}
	defer resp.Body.Close()

	// Read response body
	bodyText, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Fatal(err)
	}

	// Create and write to the file in the script's directory
	f, err := os.Create(fileName)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	_, err = f.WriteString(string(bodyText))
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("done - file saved at:", fileName)
}
