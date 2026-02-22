# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.

from pathlib import Path
from pyrogram import filters, types
from anony import anon, app, config, db, lang, queue, tg, yt
from anony.helpers import buttons, utils
from anony.helpers._play import checkUB


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"
    text = text[:1948] + "</blockquote>"
    return text


@app.on_message(
    filters.command(["play", "playforce", "vplay", "vplayforce"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    m3u8: bool = False,
    video: bool = False,
    url: str = None,
) -> None:

    # 🎬 Only GIF (No Caption)
    loading_msg = await m.reply_animation(
        animation="https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif"
    )

    file = None
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []

    if media:
        file = await tg.download(m.reply_to_message, loading_msg)

    elif m3u8:
        file = await tg.process_m3u8(url, loading_msg.id, video)

    elif url:
        if "playlist" in url:
            tracks = await yt.playlist(
                config.PLAYLIST_LIMIT, mention, url, video
            )

            if not tracks:
                await loading_msg.delete()
                return

            file = tracks[0]
            tracks.remove(file)
            file.message_id = loading_msg.id
        else:
            file = await yt.search(url, loading_msg.id, video=video)

        if not file:
            await loading_msg.delete()
            return

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        file = await yt.search(query, loading_msg.id, video=video)
        if not file:
            await loading_msg.delete()
            return

    if not file:
        await loading_msg.delete()
        return

    if file.duration_sec > config.DURATION_LIMIT:
        await loading_msg.delete()
        return

    file.user = mention

    if force:
        queue.force_add(m.chat.id, file)
    else:
        position = queue.add(m.chat.id, file)
        if position != 0 or await db.get_call(m.chat.id):
            await loading_msg.delete()
            return

    # Download if needed
    if not file.file_path:
        fname = f"downloads/{file.id}.{'mp4' if video else 'webm'}"
        if Path(fname).exists():
            file.file_path = fname
        else:
            file.file_path = await yt.download(file.id, video=video)

    # ▶️ Start Playing
    await anon.play_media(chat_id=m.chat.id, message=loading_msg, media=file)

    # ❌ Delete GIF after play starts
    try:
        await loading_msg.delete()
    except:
        pass

    if tracks:
        added = playlist_to_queue(m.chat.id, tracks)
        await app.send_message(
            chat_id=m.chat.id,
            text=f"📂 Playlist queued:\n{added}",
        )
