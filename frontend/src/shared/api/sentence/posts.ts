/* eslint-disable eslint-comments/disable-enable-pair */
/* eslint-disable prettier/prettier */
import { AxiosError, HttpStatusCode } from 'axios'
import { apiInstance } from '../api-instance'
import { uris } from '../apis'

export const parseSentense = async ({ line }: { line: string }): Promise<any> => {
	const { data } = await apiInstance.post(uris.posts.parseSentense, [
		{
			text: line
		}
	])

	if (!data.graph) {
		throw new AxiosError(data.msg, String(HttpStatusCode.BadRequest), {
      data: {
        word: data.word
      }
    } as any)
	}

	return data
}

export const findHy = async ({ word1, word2 }: { word1: string; word2: string }): Promise<any> => {
	const { data } = await apiInstance.post(uris.posts.findHy, {
    "word_1": word1,
    "word_2": word2
  })

	if (!data.graph) {
		throw new AxiosError(data.msg, String(HttpStatusCode.BadRequest), {
      data: {
        word: data.word
      }
    } as any)
	}

	return data
}


// Мама мыла раму
