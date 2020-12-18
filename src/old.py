
	def _get_subscription_id(self):
		self._last_subscription_id += 1
		return self._last_subscription_id

	async def _do_login(self, username, password):
		login_token = self.extract_login_token(await self._session.get(self.LOGIN_URL))
		self.log("login_token = " + login_token)
		login_data = get_login_data(username, password, login_token)
		old_phpsessid = self._session.cookies.get("PHPSESSID")
		r = await self._session.post(self.LOGIN_CHECK_URL, data = login_data)
		if old_phpsessid == self._session.cookies.get("PHPSESSID"):
			#self.log(r.text)
			raise ValueError("Login failed")

	async def login(self, username = None, password = None, PHPSESSID = None):
		if username != None and password != None:
			await self._do_login(username, password)
		elif PHPSESSID != None:
			self._session.cookies.set("PHPSESSID", PHPSESSID)
		else:
			raise ValueError("'username' and password' or 'PHPSESSID' should be set")


	def extract_login_token(self, response):
		response.raise_for_status()
		token = response.text
		token = token[token.index('id="_token"'):]
		token = token[token.index('value="') + len('value="'):]
		token = token[:token.index('"')]
		return token


