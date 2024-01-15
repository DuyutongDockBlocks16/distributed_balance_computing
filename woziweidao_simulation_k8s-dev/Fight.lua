package.path = package.path .. ";./fight/Lua/?.lua;"
package.path = package.path .. "./fight/Lua/?.Lua;"

-- local Fight={}
function GetTeamDataByString(teamStr)  --类似这种格式:02--1031--
	local len = string.len(teamStr)
	local team = {}
	for i = 1,5 do
		local startIndex = (i - 1)*2 + 1
		if startIndex <= len then
			local idStr = string.sub(teamStr,startIndex,startIndex + 1)
			--print(idStr)
			if idStr ~= "--" then
				local id = tonumber(idStr)
				if id == nil then
					print("error:",idStr,i,teamStr)
				else
					id = 10000000 + id
					team[i] = {id}
				end
			end
		end
	end
	return team
end

function fight(team_A, team_B, random_seed)
  -- if(team_A_index==1 and team_B_index==2 and random_seed==3) then
  --   while true do
      
  --   end
  -- end
  print("team_A: "..team_A);
  print("team_B: "..team_B);
  print("random_seed: "..random_seed);
  if type(team_A) == "string" then
		team_A = GetTeamDataByString(team_A)
	end
	if type(team_B) == "string" then
		team_B = GetTeamDataByString(team_B)
	end
	if(random_seed == nil) then
		random_seed = 1000
	end

	local status, msg = xpcall( 
		function()
			local Test = require("Test")
			local res = Test.fight(team_A, team_B, random_seed)
-- 			if(team_B_index==2) then
--                 return -1
--             end
			return res
		end,

		function (err)
			print(err)
			return -1
		end
	)
	return msg
end
-- return Fight