import heapq
import os

import pandas as pd


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_railway_data(file_path):
    """Load railway data from CSV and build an undirected weighted graph."""
    df = pd.read_csv(file_path, header=None)
    graph = {}

    for _, row in df.iterrows():
        station_a, station_b, cost, time = row[0], row[1], int(row[2]), int(row[3])
        graph.setdefault(station_a, []).append((station_b, cost, time))
        graph.setdefault(station_b, []).append((station_a, cost, time))

    return graph


def dijkstra(graph, start, end, mode="cost"):
    priority_queue = [(0, start, [])]
    visited = set()

    while priority_queue:
        current_weight, current_station, path = heapq.heappop(priority_queue)

        if current_station in visited:
            continue

        path = path + [current_station]
        visited.add(current_station)

        if current_station == end:
            return current_weight, path

        for neighbor, cost, time in graph.get(current_station, []):
            if neighbor not in visited:
                weight = cost if mode == "cost" else time
                heapq.heappush(priority_queue, (current_weight + weight, neighbor, path))

    return None


def main():
    file_path = os.path.join(BASE_DIR, "task1_3_data.csv")
    railway_graph = load_railway_data(file_path)

    departure = input("Enter departure station: ")
    destination = input("Enter destination station: ")

    while True:
        mode_input = input("Find (1) Cheapest or (2) Fastest route? Enter 1 or 2: ")
        if mode_input == "1":
            mode = "cost"
            break
        if mode_input == "2":
            mode = "time"
            break
        print("Invalid input. Please enter '1' for Cheapest or '2' for Fastest.")

    result = dijkstra(railway_graph, departure, destination, mode)

    if not result:
        print("\nNo route found between the given stations.")
        return

    total_value, route = result
    print("\nBest Route Found:")
    print(f"Total {'Cost' if mode == 'cost' else 'Time'}: {total_value}")
    print("Route:", " -> ".join(route))

    output_path = os.path.join(BASE_DIR, "train_routes.csv")
    results_df = pd.DataFrame({"Total Value": [total_value], "Route": [" -> ".join(route)]})
    results_df.to_csv(output_path, mode="a", header=not os.path.exists(output_path), index=False)
    print(f"\nResults saved to '{output_path}'")


if __name__ == "__main__":
    main()
