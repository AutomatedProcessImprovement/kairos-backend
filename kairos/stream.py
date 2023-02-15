import json
import pprint
import sseclient

PRCORE_BASE_URL = 'https://prcore.chaos.run'
PRCORE_HEADERS = {'Authorization':'Bearer UaJW0QvkMA1cVnOXB89E0NbLf3JRRoHwv2wWmaY5v=QYpaxr1UD9/FupeZ85sa2r'}

def with_requests(url, headers):
    """Get a streaming response for the given event feed using requests."""
    import requests
    return requests.get(url, stream=True, headers=headers)


def start_stream(project_id):
  print('in start stream')
  print(f'Starting the stream for project Id: {project_id}')
  URL = PRCORE_BASE_URL + f"/project/{project_id}/streaming/result"
  response = with_requests(URL,PRCORE_HEADERS)
  print('got response: ')
  print(response)
  client = sseclient.SSEClient(response)

  print("Waiting for events...")

  try:
    for event in client.events():
        if event.event == "ping":
          continue

        event_data = json.loads(event.data)
        first_event = event_data[0]
        prescriptions = first_event["prescriptions"]
        prescriptions_with_output = [prescriptions[p] for p in prescriptions if prescriptions[p]["output"]]

        if not prescriptions_with_output:
          continue
        
        print(f"Received message: {event.event}")
        print(f"ID: {event.id}")


        print(f"Data type: {type(event_data)}")
        print(f"Length: {len(event_data)}")

        pprint.pprint(prescriptions_with_output, width=120)

        print("-" * 24)
  except KeyboardInterrupt:
    print("Interrupted by user")

  print("Done!")
