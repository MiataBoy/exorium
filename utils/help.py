import discord, config
from discord.ext import commands, menus

def safe_get(list, index, default=None):
    try:
        return list[index]
    except IndexError:
        return default

class GroupHelpSource(menus.ListPageSource):
    def __init__(self, group, data):
        super().__init__(data, per_page=5)
        self.group = group

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = discord.Embed(title = str(self.group),
                              color=config.color)

        for index, command in enumerate(entries, start=offset):
            embed.add_field(name=command.qualified_name,
                            value=(
                                f"[{' | '.join([alias for alias in command.aliases])}] \n" if command.aliases else ""
                                f"{command.help or 'None'}"
                            ))

        embed.set_footer(text=f"Page {menu.current_page + 1} / {self.get_max_pages()}" if
            self.get_max_pages() > 0 else "Page 0/0")
        return embed

class CogHelpSource(menus.ListPageSource):
    def __init__(self, cog, data):
        super().__init__(data, per_page=6)
        self.cog = cog

    async def format_page(self, menu, entries):
        offset = menu.current_page * self.per_page
        embed = discord.Embed(title=self.cog.qualified_name,
                              color=config.color)

        for index, command in enumerate(entries, start=offset):
            embed.add_field(
                name=f"**{str(command)}** [{' | '.join(alias for alias in command.aliases)}]" if command.aliases else f"**{str(command)}**",
                value=(
                    f"{command.help}" or "None"
                ), inline=False
            )

        embed.set_footer(text = f"Page {menu.current_page+1} / {self.get_max_pages()}"
        if self.get_max_pages() > 0 else "Page 0/0")

        return embed

class CogHelpPages(menus.MenuPages):
    def __init__(self, source):
        super().__init__(source, delete_message_after=True)

class PenguinHelp(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={
            "cooldown": commands.Cooldown(1, 5, commands.BucketType.member),
            "help": "The help command",
            "aliases": ["h"]
        })

    async def command_not_found(self, string):
        return f"The command `{string}` was not found."

    async def send_bot_help(self, mapping):
        filtered_commands = {key: await self.filter_commands(value) for key, value in mapping.items() if getattr(key, "qualified_name", "None") != "IpcRoutes"}
        embed = discord.Embed(title = "Help",
                              description=f"Use `{self.clean_prefix}help` [command] or [module] for more help.",
                              color=config.color)
        for cog, cmds in filtered_commands.items():
            if cmds:
                embed.add_field(name = getattr(cog, "qualified_name", "None"),
                                value =f"{', '.join([f'`{command.name}`' for command in cmds])}",
                                inline=False)
        await self.get_destination().send(embed = embed)
    
    async def send_cog_help(self, cog):
        menu = CogHelpPages(source=CogHelpSource(cog, await self.filter_commands(cog.get_commands())))
        await menu.start(self.context)

    async def send_command_help(self, command):
        aliases = '`' + '`, `'.join(command.aliases) + "`"
        if aliases == "``" or aliases == '`':
            aliases = f" {config.emotecross} No aliases found"
        embed = discord.Embed(title= f"[{command.cog.qualified_name}] {command.qualified_name}", color=config.color)
            #title= command.qualified_name + " | " + " | ".join([f"{alias}" for alias in command.aliases]),
        embed.description = command.help or f"`{command.qualified_name}` does not have a description."
        embed.set_thumbnail(url=self.context.bot.user.avatar_url)
        
        command = (await self.filter_commands([command]))

        command = command[0] if len(command) == 1 else None

        if not command:
            return await self.get_destination().send(embed = embed)

        embed.add_field(name="Usage",
                        value= f"{self.clean_prefix}{command.qualified_name} {command.signature}")
        embed.add_field(name="Aliases",
                        value = aliases,
                        inline=True)
        await self.get_destination().send(embed = embed)

    async def send_group_help(self, group: commands.Group):
        menu = CogHelpPages(source=GroupHelpSource(group, await self.filter_commands(group.commands)))
        await menu.start(self.context)
