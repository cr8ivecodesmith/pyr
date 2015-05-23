"""
PyRogueCOD - A python roguelike experiment using libtcod.

"""
from __future__ import print_function

import libtcodpy as libtcod


# Global constants
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

LIMIT_FPS = 20

MAP_WIDTH = 80
MAP_HEIGHT = 45

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3

FOV_ALGO = 4  # Default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 3

color_dark_wall = libtcod.Color(0, 0, 100)
color_light_wall = libtcod.Color(130, 110, 50)
color_dark_ground = libtcod.Color(50, 50, 150)
color_light_ground = libtcod.Color(200, 180, 50)


class Tile(object):
    """ A tile on the map and its properties

    """
    def __init__(self, blocked, block_sight=None):
        self.explored = False
        self.blocked = blocked

        # By default, if a tile is blocked, it also blocks sight.
        self.block_sight = blocked if block_sight is None else block_sight


class Object(object):
    """ Generic object class

    Represents the player, monster, an item, the stairs, wall, etc. Its always
    represented by a character on the screen.

    Requires the ff. variables to be initialized prior to using this class:
    - con: off-screen console
    - map: global map coordinates
    - fov_map: FOV mapping.

    """
    def __init__(self, x, y, char, name, color, blocks=False, fighter=None,
                 ai=None):
        self.name = name
        self.blocks = blocks
        self.x = x
        self.y = y
        self.char = char
        self.color = color

        self.fighter = figher
        if self.fighter:
            # Let the fighter component know its owner.
            self.fighter.owner = self

        self.ai = ai
        if self.ai:
            # Let the ai component know its owner.
            self.ai.owner = self

    def move(self, dx, dy):
        """ Move by the given amount.

        """
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy

    def draw(self):
        """ Set the color then draw the character that represents this object
            at its position only when its within the FOV.

        """
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char,
                                     libtcod.BKGND_NONE)

    def clear(self):
        """ Erase the character that represents this object.

        """
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)


class Fighter(object):
    """ Combat-type Object component.

    """
    owner = None

    def __init__(self, hp, defense, power):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power


class BasicMonster(object):
    """ AI Object component for basic monsters

    """
    owner = None

    def take_turn(self):
        print('The {} growls!'.format(self.owner.name))


class Rect(object):
    """ A rectangle on the map used to characterize a room.

    """
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        """ All rooms will be connected via their center coordinates.

        """
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)

    def intersect(self, other):
        """ Return True if this object intersects with the `other` room.

        """
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


def create_room(room):
    """ Go through the tiles in the rectangle and make them passable.

    Requires the ff. variables to be initialized prior to calling this
    function:
    - map: global map coordinates

    """
    global map
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False


def create_h_tunnel(x1, x2, y):
    """ Carve a horizontal tunnel.

    """
    global map

    # Using the min and max creatively here, otherwise we'll have to determine
    # which one is larger or smaller to place on the appropriate range args.
    for x in range(min(x1, x2), max(x1, x2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False


def create_v_tunnel(y1, y2, x):
    """ Carve a vertical tunnel.

    """
    global map

    # Using the min and max creatively here, otherwise we'll have to determine
    # which one is larger or smaller to place on the appropriate range args.
    for y in range(min(y1, y2), max(y1, y2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False


def place_objects(room):
    """ Place objects in a room.

    Requires the ff. variables to be initialized prior to calling this
    function:
    - objects: List of game objects.

    """
    num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)

    for i in range(num_monsters):
        # NOTE: We can play around this some more to place different kinds of
        # monsters or groups of monsters. We'll settle with this for now.

        # Choose a random a place for this monster in the room.
        x = libtcod.random_get_int(0, room.x1, room.x2)
        y = libtcod.random_get_int(0, room.y1, room.y2)

        if not is_blocked(x, y):
            if libtcod.random_get_int(0, 0, 100) < 80:
                # 80% chance of an orc.
                monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green,
                                 blocks=True)
            else:
                # 20% it's a troll!
                monster = Object(x, y, 'T', 'troll', libtcod.darker_green,
                                 blocks=True)

            objects.append(monster)


def is_blocked(x, y):
    """ Check whether a location on the map has a tile or a blocking object.

    """
    if map[x][y].blocked:
        return True

    for obj in objects:
        if obj.blocks and obj.x == x and obj.y == y:
            return True

    return False


def player_move_or_attack(dx, dy):
    """ Handle player action to either move or attack

    Requires the ff. variables to be initialized prior to calling this
    function:
    - player: Object instance for the main character.
    - fov_recompute: global flag to check if FOV needs to recomputed.
    - objects: List of game objects.

    """
    global fov_recompute

    # The coordinates where the player is moving/attacking.
    x = player.x + dx
    y = player.y + dy

    # Try to find an attackable object there.
    target = None
    for obj in objects:
        if obj.x == x and obj.y == y:
            target = obj
            break

    # Attack if a target was found, move otherwise.
    if target:
        print('The {} laughs at your sorry excuse for an attack!'.format(
              target.name))
    else:
        player.move(dx, dy)
        fov_recompute = True


def handle_keys():
    """ Handle key input from the user.

    Requires the ff. variables to be initialized prior to calling this
    function:
    - player: Object instance for the main character.
    - fov_recompute: global flag to check if FOV needs to recomputed.
    - game_state: global game status to determine whether player action should
      be allowed.

    """
    global fov_recompute
    global game_state

    # Use this to make movement turn-based
    key = libtcod.console_wait_for_keypress(True)

    # Use this instead to make movement real-time
    # key = libtcod.console_check_for_keypress()

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: Toggles fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the game
        return 'exit'

    # movement
    if game_state == 'playing':
        if libtcod.console_is_key_pressed(libtcod.KEY_UP) or key.c == ord('k'):
            player_move_or_attack(0, -1)
        elif (libtcod.console_is_key_pressed(libtcod.KEY_DOWN) or
              key.c == ord('j')):
            player_move_or_attack(0, 1)
        elif (libtcod.console_is_key_pressed(libtcod.KEY_LEFT) or
              key.c == ord('h')):
            player_move_or_attack(-1, 0)
        elif (libtcod.console_is_key_pressed(libtcod.KEY_RIGHT) or
              key.c == ord('l')):
            player_move_or_attack(1, 0)
        else:
            return 'didnt-take-turn'


def make_map():
    """ Generates the map coordinates

    Creates the global var `map`.

    Room generation logic:
    Pick a random location for the first room and carve it. Then pick another
    location for the second; if it doesn't overlap with the first. Connect the
    two with a tunnel. Repeat.

    Requires the ff. variables to be initialized prior to calling this
    function:
    - player: Object instance for the main character.
    - objects: List of game objects.

    """
    global map

    # Fill map with unblocked tiles
    # Access the map: map[x][y]
    map = [[Tile(True) for y in range(MAP_HEIGHT)]
           for x in range(MAP_WIDTH)]

    rooms = []
    num_rooms = 0
    for r in range(MAX_ROOMS):
        # Random width and height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)

        # Random pos without going out of map boundaries
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

        new_room = Rect(x, y, w, h)

        # Check if the other rooms intersect with this room.
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break

        if not failed:
            # "paint" it to the map.
            create_room(new_room)

            # put objects in it such as monsters.
            place_objects(new_room)

            new_x, new_y = new_room.center()

            if num_rooms == 0:
                # If this is the first room, put the player in it.
                player.x, player.y = (new_x, new_y)
            else:
                # All rooms after the first connects to the previous room with
                # a tunnel.

                # Center coords of the previous room.
                prev_x, prev_y = rooms[num_rooms - 1].center()

                # Draw a coin (random 0 or 1)
                if libtcod.random_get_int(0, 0, 1) == 1:
                    # First move horizontally, then vertically.
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    # Do the opposite.
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)

            # Finally append the new room to the list
            rooms.append(new_room)
            num_rooms += 1


def render_all():
    """ Draw the game objects and the map.

    Requires the ff. variables to be initialized prior to calling this
    function:
    - objects: game objects list
    - map: global map coordinates
    - con: off-screen console
    - fov_recompute: global flag to check if FOV needs to recomputed.
    - fov_map: FOV mapping.

    """
    global fov_recompute

    # Recompute the FOV and reset the flag when the player moves.
    if fov_recompute:
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS,
                                FOV_LIGHT_WALLS, FOV_ALGO)

    # Go through all the tiles and set their color
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            visible = libtcod.map_is_in_fov(fov_map, x, y)
            wall = map[x][y].block_sight

            # Use the global dark or light colors depending on the visibility
            # of the tile. We also hide it until the player has explored it.
            if not visible:
                if map[x][y].explored:
                    if wall:
                        libtcod.console_set_char_background(con, x, y,
                                                            color_dark_wall,
                                                            libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y,
                                                            color_dark_ground,
                                                            libtcod.BKGND_SET)
            else:
                if wall:
                    libtcod.console_set_char_background(con, x, y,
                                                        color_light_wall,
                                                        libtcod.BKGND_SET)
                else:
                    libtcod.console_set_char_background(con, x, y,
                                                        color_light_ground,
                                                        libtcod.BKGND_SET)
                map[x][y].explored = True

    # Place the game objects on the off-screen
    for obj in objects:
        obj.draw()

    # Blit the contents of the off-screen to the main screen
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)


if __name__ == '__main__':
    """ Initialization of required variables and game loop.

    """
    global map
    global fov_recompute
    global game_state
    global player_action

    map = None
    fov_recompute = True
    game_state = 'playing'
    player_action = None

    # Set the font.
    libtcod.console_set_custom_font('terminal10x10.png',
                                    libtcod.FONT_TYPE_GREYSCALE |
                                    libtcod.FONT_LAYOUT_TCOD)

    # Init the main screen.
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT,
                              'pyroguecod tutorial', False)

    # Init an off-screen console to be used as a buffer.
    con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

    # Set FPS. This does not have an effect for turn-based games.
    libtcod.sys_set_fps(LIMIT_FPS)

    # Create the object representing the player.
    player = Object(0, 0, '@', 'player', libtcod.white, blocks=True)

    # Init list of game objects.
    objects = []

    # Generate map coordinates.
    make_map()

    # We make sure that the player is the last item in the object list.
    objects.append(player)

    # Initalize the FOV map.
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y,
                                       not map[x][y].block_sight,
                                       not map[x][y].blocked)

    while not libtcod.console_is_window_closed():
        # Render the screen.
        render_all()

        libtcod.console_flush()

        # Clear characters on the off-screen
        for obj in objects:
            obj.clear()

        # handle keys and exit the game if needed
        player_action = handle_keys()

        if player_action == 'exit':
            break

        # Let monsters take their turn
        if game_state == 'playing' and player_action != 'didnt-take-turn':
            for obj in objects:
                if obj != player:
                    print('The {} growls!'.format(obj.name))
