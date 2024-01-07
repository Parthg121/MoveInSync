class MeetingRoom:
    def __init__(self, room_id, capacity, location, floor):
        self.room_id = room_id
        self.capacity = capacity
        self.location = location
        self.floor = floor
        self.is_booked = False
        self.last_booked_by = None

    def book(self, user):
        if not self.is_booked:
            self.is_booked = True
            self.last_booked_by = user
            return True
        else:
            return False

    def release(self):
        if self.is_booked:
            self.is_booked = False
            return True
        else:
            return False

class User:
    def __init__(self, name):
        self.name = name
        self.booking_history = {}

    def add_booking(self, room):
        if room.room_id not in self.booking_history:
            self.booking_history[room.room_id] = 1
        else:
            self.booking_history[room.room_id] += 1

        # Sort the booking history based on the number of times each room was booked
        self.booking_history = dict(sorted(self.booking_history.items(), key=lambda x: x[1], reverse=True))

class MeetingRoomBookingSystem:
    def __init__(self):
        self.meeting_rooms = {}

    def add_meeting_room(self, room_id, capacity, location, floor):
        room = MeetingRoom(room_id, capacity, location, floor)
        self.meeting_rooms[room_id] = room

    def suggest_meeting_room(self, participants, location, preferred_floor=None, user=None):
        available_rooms = [room for room in self.meeting_rooms.values() if not room.is_booked and room.capacity >= participants and room.location == location]

        if user:
            user_last_booked_rooms = list(user.booking_history.keys())
            user_last_booked_available_rooms = [room for room in user_last_booked_rooms if room in available_rooms]
            suggested_rooms = user_last_booked_available_rooms + [room for room in available_rooms if room not in user_last_booked_rooms]
        else:
            suggested_rooms = available_rooms

        if preferred_floor:
            suggested_rooms = sorted(suggested_rooms, key=lambda x: (x.room_id in user_last_booked_available_rooms, abs(x.floor - preferred_floor)))

        return suggested_rooms

    def book_meeting_room(self, room_id, user):
        room = self.meeting_rooms.get(room_id)

        if room:
            if room.book(user):
                user.add_booking(room)
                return True
            else:
                return False
        else:
            raise ValueError("Meeting room not found.")

    def release_meeting_room(self, room_id):
        room = self.meeting_rooms.get(room_id)

        if room:
            if room.release():
                return True
            else:
                return False
        else:
            raise ValueError("Meeting room not found.")

# Example Usage
booking_system = MeetingRoomBookingSystem()
booking_system.add_meeting_room("A101", 10, "Building A", 1)
booking_system.add_meeting_room("A102", 15, "Building A", 2)
booking_system.add_meeting_room("B201", 20, "Building B", 1)
booking_system.add_meeting_room("B202", 25, "Building B", 2)

user = User("User123")

try:
    preferred_floor = int(input("Enter preferred floor (or press Enter to ignore): ") or 0)
    suggested_rooms = booking_system.suggest_meeting_room(participants=10, location="Building A", preferred_floor=preferred_floor, user=user)
    if suggested_rooms:
        print("Suggested Rooms:")
        for room in suggested_rooms:
            print(f"Room: {room.room_id}, Capacity: {room.capacity}, Location: {room.location}, Floor: {room.floor}")
        user_last_booked_rooms = list(user.booking_history.keys())
        print(f"User's Last Booked Rooms: {user_last_booked_rooms}")
    else:
        print("No available meeting rooms.")
except ValueError as e:
    print(f"Error: {e}")

# Output:
# Enter preferred floor (or press Enter to ignore): 2
# Suggested Rooms:
# Room: A102, Capacity: 15, Location: Building A, Floor: 2
# Room: A101, Capacity: 10, Location: Building A, Floor: 1
# User's Last Booked Rooms: []

# Release the booked room after the meeting
try:
    booking_system.release_meeting_room("A102")
    print("Meeting room released successfully.")
except ValueError as e:
    print(f"Error: {e}")