import re
import asyncio
import aiohttp
from config import Config


class EmailVerificationHandler:
    def __init__(self):
        self.username = Config().get_temp_mail()
        self.emailExtension = "@mailto.plus"
        self.session = None
        self.code = None

    async def get_verification_code(self):
        """获取验证码的主方法"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            print("正在处理...")
            code, first_id = await self._get_latest_mail_code()
            print(f"最新邮件ID: {first_id} and 验证码: {code}")
            if first_id:
                await self._cleanup_mail(first_id)
            self.code = code
            return code
        except Exception as e:
            print(f"获取验证码失败: {str(e)}")
            return None
        finally:
            if self.session:
                await self.session.close()
                self.session = None

    async def _get_latest_mail_code(self):
        mail_list_url = f"https://tempmail.plus/api/mails?email={self.username}{self.emailExtension}&limit=20&epin="

        async with self.session.get(mail_list_url) as response:
            mail_list_data = await response.json()

        if not mail_list_data.get("result"):
            return None, None

        first_id = mail_list_data.get("first_id")
        if not first_id:
            return None, None

        mail_detail_url = f"https://tempmail.plus/api/mails/{first_id}?email={self.username}{self.emailExtension}&epin="
        async with self.session.get(mail_detail_url) as response:
            mail_detail_data = await response.json()

        if not mail_detail_data.get("result"):
            return None, None

        mail_text = mail_detail_data.get("text", "")
        code_match = re.search(r"\b\d{6}\b", mail_text)
        return (code_match.group(), first_id) if code_match else (None, None)

    async def _cleanup_mail(self, first_id):
        if not first_id:
            return False

        delete_url = "https://tempmail.plus/api/mails/"
        payload = {
            "email": f"{self.username}{self.emailExtension}",
            "first_id": first_id,
            "epin": "",
        }

        try:
            async with self.session.delete(delete_url, data=payload) as response:
                result = (await response.json()).get("result")
                return result is True
        except:
            return False

    def _return_code(self, code):
        return code

    def get_code(self):
        """同步方法获取验证码"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            code = loop.run_until_complete(self.get_verification_code())
            return code
        finally:
            loop.close()


# 测试代码
async def main():
    async with EmailVerificationHandler() as handler:
        code = await handler.get_verification_code()
        print(f"获取到的验证码: {code}")


if __name__ == "__main__":
    asyncio.run(main())
