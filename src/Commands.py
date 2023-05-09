import inspect
from Temp import clients, send_data, banned_users, user_leave, channels, Channel

# more commands.
# + ban
# + banned-users
# + users
# + user-count
# + much better and improved error handling, covers all cases (hopefully)


class Commands:
    prefix = "//"
    commands = {}
    killed_commands = set()

    def command(name: str, permission=1):
        def wrapper(command):
            Commands.commands[name] = [command, permission]
            return command

        return wrapper


async def help_text():
    text = f"""
    Commnads:
        {Commands.prefix}help   ->  returns a useful list of available commands and their usages.
        {Commands.prefix}create-channel <channel name>  ->   Creates a channel with the specified name.
        {Commands.prefix}join-channel <channel name>   ->  Joins specified channel.
        {Commands.prefix}leave-channel  ->  leaves the current channel you are in. 
        {Commands.prefix}delete-channel <channel name>   ->  Deletes the specified channel name if it exists.
        {Commands.prefix}users  ->  returns a list of all online users in the server.
        {Commands.prefix}user-count     ->  returns a numeric amount of users online.
        {Commands.prefix}banned-users   ->  returns a list of all banned-users.
        {Commands.prefix}broadcast <message>    ->  broadcasts a message as the server.
        {Commands.prefix}ban <username> (reason)    ->  bans a user with an optional reason.
        {Commands.prefix}unban <username> ->    unbans a specified user.
        {Commands.prefix}disable-command <command name>     ->  diables the specified command.
        {Commands.prefix}enable-command <command name>  ->  enables the specified command."""
    return text


async def check_command(client, message: str):
    try:
        """Checks if the command usage is valid and if it is an actual command"""
        message = message.removeprefix(
            Commands.prefix
        ).split()  # removes the command prefix from the message
        function_name = message[0]
        if function_name in Commands.commands:
            if function_name in Commands.killed_commands:
                return f"Command: {function_name} is disabled."
            function = Commands.commands[function_name][0]
        else:
            return f"Command: {function_name}, not found"

        function_data = inspect.getfullargspec(function)
        args = function_data.args
        varargs = function_data.varargs

        if "client" in args:
            args.remove("client")

        if len(message) > 1:
            parameters = message[1:]

            if len(parameters) < len(args):
                missing_parameters = args[len(parameters) :]
                return f"Missing parameter(s): {', '.join(missing_parameters)}"

            if varargs:
                # print(varargs)
                arg_parameters = parameters[: len(args)]
                varargs_parameters = parameters[len(args) :]
                await function(client, *arg_parameters, *varargs_parameters)
            else:
                # print(parameters)
                await function(client, *parameters)
        elif args or varargs:
            return f"Missing parameter(s): {', '.join(args)}"

        else:
            await function(client)
    except TypeError as e:
        return f"Invalid usage: {str(e)}"
    except Exception as e:
        return f"Error occurred: {str(e)}"


@Commands.command("broadcast", 5)
async def broadcast(client, *message):
    if len(message) > 0:
        message = " ".join(message)
    format = {"sender": "Server", "message": message, "message_type": "public"}
    for client in clients.values():
        await send_data(client, format)


@Commands.command("users", 5)
async def users_online(client):
    user_list = [x for x in clients.keys()]
    message = f"Users online: {user_list}"
    format = {"sender": "Server", "message": message, "message_type": "public"}
    await send_data(client, format)


@Commands.command("channels", 5)
async def get_channels(client):
    channel_list = [x for x in channels.keys()]
    message = f"Channels: {channel_list}"
    format = {"sender": "Server", "message": message, "message_type": "public"}
    await send_data(client, format)


@Commands.command("user-count", 5)
async def users_online(client):
    message = f"Number of users online: {len(clients)}"
    format = {"sender": "Server", "message": message, "message_type": "public"}
    await send_data(client, format)


@Commands.command("banned-users", 5)
async def users_banned(client):
    # will be combined with users function eventually
    """Sends a list of all banned users"""
    banned_list = [x for x in banned_users]
    message = f"Banned Users: {banned_list}"
    format = {"sender": "Server", "message": message, "message_type": "public"}
    await send_data(client, format)


@Commands.command("ban", 1)
async def ban_user(client, *data):
    format = {
        "sender": "Server",
        "message": "You have been banned!",
        "message_type": "private",
    }
    target_username = data[0]
    if target_username in clients:
        target_client = clients[target_username]
        data = data[1 : len(data)]
    elif target_username in banned_users:
        format["message"] = "User is already banned."
        await send_data(client, format)
        return
    else:
        format["message"] = "User not found."
        await send_data(client, format)
        return

    if len(data) >= 1:
        data = " ".join(data)
        format["message"] = f"You have been banned for: {data}"

    await send_data(target_client, format)

    banned_users.add(target_username)
    await user_leave(target_client)
    format["message"] = f"{target_username} has been banned."
    await send_data(client, format)


@Commands.command("unban", 1)
async def unban_user(client, *data):
    format = {"sender": "Server", "message": "", "message_type": "private"}
    target_username = data[0]
    if target_username in banned_users:
        banned_users.remove(target_username)
        format["message"] = f"{target_username} has been unbanned."
        await send_data(client, format)

    elif target_username in clients:
        format["message"] = "User is not banned."
        await send_data(client, format)
        return
    else:
        format["message"] = "User not found."
        await send_data(client, format)
        return


@Commands.command("help", 5)
async def help(client):
    message = await help_text()
    format = {
        "sender": "Server",
        "message": f"Commands: {message}",
        "message_type": "private",
    }
    await send_data(client, format)


@Commands.command("set-prefix", 5)
async def change_prefix(client, prefix):
    Commands.prefix = prefix
    format = {
        "sender": "Server",
        "message": f"Prefix has been changed to: {prefix}",
        "message_type": "private",
    }
    await send_data(client, format)


@Commands.command("disable-command", 5)
async def turn_off_command(client, command_name):
    format = {"sender": "Server", "message": "", "message_type": "private"}
    if command_name in Commands.commands:
        if command_name not in Commands.killed_commands:
            Commands.killed_commands.add(command_name)
            format["message"] = f"{command_name} has been disabled."
        else:
            format["message"] = f"{command_name} is already disabled."
    else:
        format["message"] = f"{command_name} not found."

    await send_data(client, format)


@Commands.command("enable-command", 5)
async def turn_on_command(client, command_name):
    format = {"sender": "Server", "message": "", "message_type": "private"}
    if command_name in Commands.commands:
        if command_name in Commands.killed_commands:
            Commands.killed_commands.remove(command_name)
            format["message"] = f"{command_name} has been enabled."
        else:
            format["message"] = f"{command_name} is already enabled."
    else:
        format["message"] = f"{command_name} not found."

    await send_data(client, format)


@Commands.command("join-channel", 5)
async def join_channel(client, channel_name):
    format = {"sender": "Server", "message": "", "message_type": "private"}
    if channel_name in channels.keys():
        channel = channels[channel_name]
        if client in channel.clients:
            format["message"] = f"You are already in this channel."
        else:
            format["message"] = f"You have joined the channel named, {channel_name}."
            client.current_channel = channel
            channel.clients.add(client)
    else:
        format["message"] = f"The channel {channel_name}, does not exist."

    await send_data(client, format)


@Commands.command("leave-channel", 5)
async def leave_channel(client):
    format = {"sender": "Server", "message": "", "message_type": "private"}
    if client.current_channel is not None:
        channel = client.current_channel
        channel.clients.remove(client)
        client.current_channel = None
        format["message"] = f"You have left the channel."
    else:
        format["message"] = f"You are not in a channel."

    await send_data(client, format)


@Commands.command("create-channel", 5)
async def create_channel(client, channel_name):
    format = {"sender": "Server", "message": "", "message_type": "private"}
    if channel_name in channels.keys():
        format["message"] = f"The channel {channel_name}, already exists."
    else:
        channel = Channel(channel_name)
        channels[channel_name] = channel
        format["message"] = f"The channel {channel_name}, has been created."

    await send_data(client, format)


@Commands.command("delete-channel", 5)
async def delete_channel(client, channel_name):
    format = {"sender": "Server", "message": "", "message_type": "private"}
    if channel_name in channels.keys():
        channel = channels[channel_name]
        for client in channel.clients:  # removes all users
            client.current_channel = None
        del channels[channel_name]
        format["message"] = f"The channel {channel_name} has been deleted."
    else:
        format["message"] = f"The channel {channel_name} does not exist."

    await send_data(client, format)
